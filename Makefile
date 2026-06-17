#!make

CONTAINER_NAME := ssmcp
IMAGE_NAME     := ssmcp

build:
	docker build --no-cache=false -t ${IMAGE_NAME} .

exec:
	docker stop ${CONTAINER_NAME}
	docker rm   ${CONTAINER_NAME}
	docker run --name ${CONTAINER_NAME}  --restart unless-stopped -v ./SoaringSpot:/app/SoaringSpot/ -d -p 9009:9009 ${IMAGE_NAME} 

clean:
	docker stop ${CONTAINER_NAME} 
	docker rm   ${CONTAINER_NAME} 
	docker rmi  ${IMAGE_NAME} 
	docker images

