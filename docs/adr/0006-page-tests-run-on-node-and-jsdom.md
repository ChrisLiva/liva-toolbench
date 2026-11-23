# crank-pilot's page tests run on Node with jsdom

crank-pilot's page modules are tested with `node --test` against jsdom, so a refactor of the page is held by tests the gate runs rather than by a browser probe or a person clicking through. jsdom is the repo's first npm dependency: a private root `package.json` pins it exactly as a devDependency and `node_modules/` stays gitignored, so no plugin folder ships it. The gate fails with a line asking for `npm ci` when it is missing, instead of reaching the network itself.
