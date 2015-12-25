Tarrasch uses Slack's real-time messaging API for everything. This means that it does everything over websockets and does not receive any traditional HTTP traffic. As a result of this, Tarrasch doesn't play particularly nicely with Heroku's free dynos, since the Tarrasch dyno will never go to sleep.

If you want to use free dynos, it's sufficient to schedule some cron jobs somewhere to scale the bot up and down. Here's a cheatsheet for what you need to do:

### Figure out your formation ID

```
curl -n -X GET https://api.heroku.com/apps/$APP_NAME/formation \
-H "Authorization: Bearer $HEROKU_API_TOKEN"
-H "Accept: application/vnd.heroku+json; version=3"
```

This will give you some JSON including information for the bot dyno running Tarrasch. Note the formation ID.

### Scaling your dyno up and down

```
curl -n -X PATCH https://api.heroku.com/apps/$APP_NAME/formation/$FORMATION_ID \
-H "Accept: application/vnd.heroku+json; version=3" \
-H "Authorization: Bearer $HEROKU_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "quantity": $DESIRED_QUANTITY_PROBABLY_0_OR_1,
  "size": "Free"
}'
```

To comply with Heroku's free dyno policies, you'll need to sleep Tarrasch for 6 hours a day.
