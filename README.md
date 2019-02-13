# cadre_familial
Monitor an email account and push attachments to dropbox

## Runbook
### Connect to redis container from VM

`docker run -it --link cadrefamilial_redis_1:redis --net cadrefamilial_default --rm redis:alpine redis-cli -h redis -p 6379`

## Restore redis data
`docker cp dump2018_10_12.rdb cadrefamilial_redis_1:/data/dump.rdb`
