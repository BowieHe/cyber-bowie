# @cyber-bowie/pi-skills-search

Portable deep-search skill extracted from the `finpal` search workflow.

## What is copied

The original `finpal` implementation is preserved at:

- `reference/fund-deep-search.original.ts`

## What is adapted

The portable implementation in `src/index.ts` keeps the core ideas:

- gap-aware query generation
- duplicate filtering
- lightweight research board
- confidence and gap detection

But it removes hard dependencies on `finpal` internals like:

- `smartSearch`
- `webAgent`
- custom logger

## Runtime contract

Provide a runtime with:

- `search(query)` for fetching search results
- optional `enrich(...)` for deeper extraction
- optional `log(...)`

## Finpal migration sketch

In `finpal`, you can replace the local skill with:

```ts
import { createFinpalCompatibleSearchSkill } from "@cyber-bowie/pi-skills-search";

export const fundDeepSearchSkill = createFinpalCompatibleSearchSkill({
  search: async (query) => {
    const results = await smartSearch(query);
    return results.map((item) => ({
      title: item.title,
      url: item.url || item.link,
      snippet: item.description || item.snippet,
      source: item.engine,
    }));
  },
  enrich: async ({ entity, acceptedResults }) => {
    const webResult = await webAgent({
      entity,
      searchResults: acceptedResults,
    });

    return {
      summary: webResult.summary,
    };
  },
});
```
