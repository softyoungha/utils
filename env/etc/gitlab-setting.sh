# rpm 설치
sudo rpm -ivh gitlab-runner_amd64.rpm

# 재설정
sudo gitlab-runner uninstall

# working directory 설정
sudo gitlab-runner install --working-directory /home/ec2-user/src --user youngha

# gitlab-runner 재부팅
sudo service gitlab-runner restart

# one line command
sudo gitlab-runner register \
   --non-interactive \
   --url http://gitlab-url/ \
   --clone-url http://gitlab-url \
   --registration-token Q9wL3d3nEkJcJDoxfygA \
   --name "$(hostname)" \
   --tag-list "deploy,${MARS__ENV,,},$(hostname)" \
   --executor shell

# 직접 입력시
sudo gitlab-runner register
# gitlab address: http://gitlab-url/
# token(2021-03-02): Q9wL3d3nEkJcJDoxfygA
# deploy,{dev/prd}, ${hostname -i}
# shell
# https://docs.gitlab.com/runner/configuration/advanced-configuration.html#the-runners-section

# clone_url 설정 필수!!!
sudo vi /etc/gitlab-runner/config.toml

# [[runner]]
#  ...
#  clone_url = "http://gitlab-url"
#  ...

# gitlab-runner 재부팅
sudo service gitlab-runner restart

# unregister
sudo gitlab-runner unregister --name "$(hostname)"