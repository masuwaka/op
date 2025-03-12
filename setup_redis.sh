#!/bin/bash

apt install redis
sed -i.bak "s/^\(port \)6379$/\156379/" /etc/redis/redis.conf
sed -i.bak "s/^# \(requirepass \).*$/\1passwd/" /etc/redis/redis.conf
systemctl restart redis-server