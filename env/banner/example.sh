#!/bin/bash

# 서버 시작시 BANNER 추가(motd)
# sudo vi /etc/profile.d/motd.sh && sudo chmod 755 /etc/profile.d/motd.sh
# http://patorjk.com/software/taag/#p=display&f=Contessa&t=DATA

Black="\033[0;30m"
Red="\033[0;31m"
Green="\033[0;32m"
Blue="\033[0;34m"
Purple="\033[0;34m"
Cyan="\033[0;35m"
Silver="\033[0;36m"
DarkGray="\033[1;30m"
LightBlue="\033[1;34m"
LightGreen="\033[1;32m"
LightCyan="\033[1;36m"
LightRed="\033[1;31m"
Yellow="\033[1;33m"
White="\033[1;37m"
X="\033[0;0m"

echo -e "${Red}     .__ .__..___..__.     ${X}"
echo -e "${Red}___  |  \[__]  |  [__]  ___${X}"
echo -e "${Red}     |__/|  |  |  |  |     ${X}"
echo -e ""
echo -e "${White}$(hostname) $(hostname -I | awk '{ print $1 }')${X}"
echo -e "login as ${White}$USER${X}"
