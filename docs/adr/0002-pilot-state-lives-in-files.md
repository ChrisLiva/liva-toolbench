# crank-pilot keeps its session state in files, not in the server

crank-pilot shows one page per effort through a long-lived local server. Every interaction and response is a file under `.crank/<slug>/` and the server holds no state, so a crashed server or a fresh agent session resumes from disk and the files double as the structured record agents read. A one-shot command per interaction was simpler but could not keep one page open through a phase.
