#!/usr/bin/env bash

if ! type "heroku" > /dev/null 2>&1 ; then
   echo "heroku CLI is not installed"
   exit
fi

heroku login

heroku create

heroku addons:create scheduler:standard

git push heroku main

heroku config:push

heroku addons:open scheduler