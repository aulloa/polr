# polr
A minimal project to scrape indeed for salary estimates for skill queries. Check main for some classes and functions useful for doing so.

## How does it work
It takes skills seperated by spaces(maximum 20), creates combinations of them(maximum 4 skills per combination) and queries indeed. It takes the estimated salary data from the web page returned and performs a weighted average. Then graphs the data using matplot lib. The Color Coded graph is a visual represenetation of both top graphs as one.

