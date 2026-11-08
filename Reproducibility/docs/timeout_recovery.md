# Final-arm timeout recovery

The first seed-44 one-round attempt stopped at training item 21 with APITimeoutError after 188 successful calls. No complete final evaluation was produced. The request timeout was raised from 90 to 240 seconds for the restart, without changing prompts, data, generation limits or learning parameters. Automatic retries remain disabled. Both unsuccessful attempts remain in the project cost accounting and raw evidence. The restart was motivated by transport failure, not accuracy.
