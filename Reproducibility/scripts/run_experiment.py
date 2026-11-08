"""Run unmodified ACE logic through a fail-closed, serial API adapter."""
import argparse
import hashlib
import json
import os
import math
import inspect
import threading
import uuid
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(ROOT / '.cache/tiktoken'))
sys.path.insert(0, str(ROOT / 'upstream/ace-main'))

class StopExperiment(BaseException):
    """Bypass upstream broad Exception handlers on billing/transport failures."""

class Meter:
    def __init__(self, input_rate, output_rate, ceiling):
        if not all(math.isfinite(v) for v in (input_rate, output_rate, ceiling)) or input_rate <= 0 or output_rate <= 0 or not 0 < ceiling <= 100:
            raise ValueError('Rates must be positive; ceiling must be <= CNY 100')
        self.rates = input_rate, output_rate
        self.ceiling = ceiling
        self.path = ROOT / 'results/budget.jsonl'
        self.path.parent.mkdir(exist_ok=True)
        self.spent = sum(json.loads(s)['reserved_cny'] for s in self.path.read_text().splitlines()) if self.path.exists() else 0
        self.lock = threading.Lock()

    def reserve(self, prompt, max_tokens):
        # UTF-8 bytes bound byte-based token counts conservatively; include framing.
        amount = ((len(prompt.encode('utf-8')) + 4096) * self.rates[0] + max_tokens * self.rates[1]) / 1e6
        with self.lock:
            if self.spent + amount > self.ceiling:
                raise StopExperiment('Budget reservation would exceed ceiling')
            self.spent += amount
            request_id = str(uuid.uuid4())
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps({'time': time.time(), 'request_id': request_id, 'reserved_cny': amount, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}) + '\n')
        return request_id, amount

    def settle(self, reservation, usage):
        if not usage:
            return  # Unknown usage keeps the entire reservation charged.
        actual_upper = (usage.prompt_tokens * self.rates[0] + usage.completion_tokens * self.rates[1]) / 1e6
        delta = actual_upper - reservation[1]
        with self.lock:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps({'time': time.time(), 'settles': reservation[0], 'reserved_cny': delta, 'usage_cost_upper_cny': actual_upper}) + '\n')
            self.spent += delta
            if self.spent > self.ceiling:
                raise StopExperiment('Provider usage exceeded conservative reservation; stopping')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['pilot', 'main'], default='pilot')
    p.add_argument('--arm', choices=['base', 'ace_r3', 'ace_r1'], required=True)
    p.add_argument('--seed', type=int, choices=[42,43,44], default=42)
    p.add_argument('--model', required=True)
    p.add_argument('--input-cny-million', type=float, required=True, help='Verified cache-miss rate')
    p.add_argument('--output-cny-million', type=float, required=True)
    p.add_argument('--workers', type=int, default=1)
    args = p.parse_args()
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise SystemExit('Set DEEPSEEK_API_KEY locally; do not paste it in logs.')
    from openai import OpenAI
    client = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'], base_url='https://api.deepseek.com', max_retries=0, timeout=240)
    meter = Meter(args.input_cny_million, args.output_cny_million, 5 if args.phase == 'pilot' else 95)
    destination = ROOT / 'results' / f'{args.phase}_{args.arm}_{args.seed}_{time.time_ns()}'
    destination.mkdir()
    (destination / 'settings.json').write_text(json.dumps({**vars(args), 'started_at': time.time()}, indent=2))
    usage_lock = threading.Lock()
    def create(**kw):
        prompt = kw['messages'][0]['content']
        reservation = meter.reserve(prompt, kw.get('max_tokens', 2048))
        stage, role, call_id = 'unknown', 'unknown', 'unknown'
        for frame in inspect.stack():
            if frame.function == 'timed_llm_call':
                role = frame.frame.f_locals.get('role')
                call_id = frame.frame.f_locals.get('call_id')
            if frame.function == '_train_single_sample':
                stage = 'adaptation'
            elif frame.function == '_offline_train' and stage == 'unknown':
                stage = 'validation'
            elif frame.function == '_run_test':
                stage = frame.frame.f_locals.get('prefix', 'test')
        kw['extra_body'] = {'thinking': {'type': 'disabled'}}
        started = time.time()
        try:
            response = client.chat.completions.create(**kw)
        except Exception as exc:
            raise StopExperiment(f'API stopped: {type(exc).__name__}, HTTP {getattr(exc, "status_code", None)}; inspect provider balance/status before resuming') from None
        meter.settle(reservation, response.usage)
        with usage_lock, (destination / 'usage.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'model': response.model, 'stage': stage, 'role': role, 'call_id': call_id, 'latency_s': time.time()-started, 'finish_reason': response.choices[0].finish_reason if response.choices else None, 'usage': response.usage.model_dump() if response.usage else None}) + '\n')
        return response
    proxy = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    import utils
    utils.initialize_clients = lambda provider: (proxy, proxy, proxy)
    from ace import ACE
    from eval.finance.data_processor import DataProcessor, load_data
    processor = DataProcessor('formula')
    folder = ROOT / 'data' / args.phase / str(args.seed)
    datasets = {s: processor.process_task_data(load_data(str(folder / (s+'.jsonl')))) for s in ['train','val','test']}
    system = ACE(api_provider='deepseek', generator_model=args.model, reflector_model=args.model, curator_model=args.model, max_tokens=2048, use_bulletpoint_analyzer=False)
    config = dict(num_epochs=1, max_num_rounds=1 if args.arm == 'ace_r1' else 3, curator_frequency=1, eval_steps=len(datasets['train']), save_steps=10, playbook_token_budget=80000, task_name='formula', json_mode=False, no_ground_truth=False, save_dir=str(destination), test_workers=args.workers, use_bulletpoint_analyzer=False, api_provider='deepseek')
    system.run(mode='eval_only' if args.arm == 'base' else 'offline', train_samples=datasets['train'], val_samples=datasets['val'], test_samples=datasets['test'], data_processor=processor, config=config)
    (destination / 'completed.json').write_text(json.dumps({'completed_at': time.time()}))

if __name__ == '__main__':
    # Prevent concurrent processes from racing the shared persistent ledger.
    lock = ROOT / 'results/.run.lock'
    lock.parent.mkdir(exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit('Another run or stale lock exists; inspect before resuming.')
    try:
        main()
    except StopExperiment as exc:
        raise SystemExit(str(exc))
    finally:
        os.close(fd)
        lock.unlink()
