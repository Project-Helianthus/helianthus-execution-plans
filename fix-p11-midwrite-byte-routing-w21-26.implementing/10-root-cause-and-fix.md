# Historical root cause and correction

Under bus contention, a gateway transmission could appear to win arbitration while the
first observed wire byte belonged to another initiator. The former strict echo filter
dropped that byte before the bus collision classifier could see it. The active request
then timed out instead of following its existing collision recovery path.

The historical correction forwarded only an unexpected master-class byte at the first
transmitted position before any echo matched. The bus layer then classified the condition
as a collision and used its existing retry behavior. It did not relax filtering for later
bytes or arbitrary noise.

The correction did not resolve missing later echoes or response-phase interleaving. M4
remained NO_GO because the required contention floor was not observed. Further work needs
a separate plan and repository-local tests.
