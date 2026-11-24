# crank-pilot vendors its rendering libraries

crank-pilot's page ships markdown-it, mermaid and highlight.js as pinned files inside the plugin and loads nothing from a CDN, so the page works offline and a session never depends on a third-party host. This departs from crank-deepen's report, which loads mermaid from a CDN, and costs about 3.8 MB of minified JavaScript in the repo.
