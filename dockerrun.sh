docker stop ssmcp
docker rm ssmcp
docker run --name ssmcp --restart unless-stopped -v ./SoaringSpot:/app/SoaringSpot/ -d -p 9009:9009 ssmcp
