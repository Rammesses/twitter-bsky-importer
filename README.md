# Twitter BSKY Importer

This project aims to be a turnkey solution to migrating your twitter data export into BlueSky posts.

## Getting Started

1. Use the `install-prereqs.sh` script to install all the pre-reqs 
2. Start the MongoDB and Mongo-Express containers using `docker compose up -d`
3. Import your twitter export `.zip` file using `/import.sh my_twitter_export.zip`
4. Sync up to Bluesky using `./sync.sh`

