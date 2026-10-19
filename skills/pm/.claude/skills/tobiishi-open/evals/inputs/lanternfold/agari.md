# 上がり Agari — lanternfold's "done"

lanternfold serves a small set of pages to a signed-in reader. It is done when every page carries the
headers its own view asks for, and no page has to be special-cased at the edge.

**Reached when** all hold:

1. Each view states its own header set, and the edge writes exactly the pairs it is handed.
2. Every page response is served with the headers it carries today, byte for byte.
