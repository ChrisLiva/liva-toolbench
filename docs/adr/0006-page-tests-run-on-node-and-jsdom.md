# crank-pilot's page tests run on Node with jsdom

crank-pilot's page modules are tested with `node --test` against jsdom, so a refactor of the page is held by tests the gate runs rather than by a browser probe or a person clicking through. jsdom is pinned exactly as a devDependency of a private root `package.json`, which pnpm locks in `pnpm-lock.yaml`, and `node_modules/` stays gitignored, so no plugin folder ships it. The gate fails with a line asking for `pnpm install --frozen-lockfile` when it is missing, instead of reaching the network itself.
