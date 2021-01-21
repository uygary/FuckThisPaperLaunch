# FuckThisPaperLaunch

Shitty script for purchasing a Ryzen 9 5950X on Amazon.  
Looks like I'll eventually end up adding more integrations thanks to the paper launch and cancelled orders due to lack of stock.

None of this shit is tested that well really, and I haven't quite touched Python for 2 decades, so you're on your own if things go south.
Keep in mind that it ignores currency, so set your prices and item links carefully.
Since I work with PowerShell, the scripts and these instructions are based on that, but of course you could use any shell you want in order to run this.  
There's a bunch of issues around break handling. And still more refactor to do around multiple buyer implementations.

---

## Populate `.env` file
This step is necessary only on the first run.


```
PS D:\CODE\FuckThisPaperLaunch> cp .\.env.sample .\.env
```
Then edit the `.env` file to update these values:  
`NUMBER_OF_ITEMS` (How many items you're trying to buy.)  
`ENABLED_BUYERS` This is a comma separated list of buyers we want running. Currently valid values are: `AmazonBuyer` and `WalmartBuyer`  
We default to Amazon only. If you want to try WalmartBuyer as well, you'll need to raise the `TIMEOUT_IN_SECONDS` setting to some crazy high value just for a glimmer of hope to avoide the aggressive captcha challenges.  
`NeweggBuyer` is currently being worked on as well, but I feel uneasy about that particular integration since Newegg keeps asking for the fucking CVV2 code.  

`ITEM_NAME_1` (Just for logging purposes.)  
`MAX_BUY_COUNT_1`  
`MAX_COST_PER_ITEM_1` (his is total cost per item, including taxes and shipping. Beware: Currency is ignored.)  
`AMAZON_LOGIN_EMAIL_1` (You should use separate accounts for each item you're trying to buy.)  
`AMAZON_LOGIN_PASSWORD_1`  
Feel free to change the `AMAZON_ITEM_ENDPOINT_1` setting as well according to what you're actually trying to buy. There are some example endpoints in the environment file.  
If you have more items to buy, keep editing and/or adding new entries for each of these configuration values that are suffixed with `2`, `3`, etc.  

With the addition of WalmartBuyer implementation, these values have been added as well, so if want to enable Walmart, update them accordingly:  
`WALMART_WHITELISTED_SELLERS`, `WALMART_LOGIN_EMAIL_1`, `WALMART_LOGIN_PASSWORD_1`, `WALMART_ITEM_ENDPOINT_1`

Update the `IS_TEST_RUN` value to `False` when you're happy with the settings.  The script will not actually buy anything as long as this is set to `True`.

## Set Chrome driver version
Modify the `chromedriver-py` version in `requirements.txt` to match your Chrome version.
You should stick to the latest version that has the same **major** version with your browser.
ie. If your Chrome version is `87.0.4280.141`, you should use `87.0.4280.88` of chromedriver-py since that is the latest driver of the `87.x.x.x` series available. You should not use 88.0.4324.27 since it won't be able to connect to Chrome 87.
Available versions can be [seen here.](https://pypi.org/project/chromedriver-py/#history)

## Install dependencies
This step is necessary only on the first run.


Open up a PowerShell prompt. (Windows Terminal, ConEmu, or just a PS prompt)
Then run the `init.ps1` script.

```
PS D:\CODE\FuckThisPaperLaunch> .\init.ps1
```
This will basically initialize a virtual environment, activate it, and install dependencies.

---

## Run
On the same PowerShell prompt just run the `start.ps1` script.

```
PS D:\CODE\FuckThisPaperLaunch> .\start.ps1
```
This will simply run the script.
Of course you could just use PyCharm Community Edition or Visual Studio to run this if you wanna fiddle around with the code and debug it.

In order to stop the bot, just press `CRTL`+`C` and wait for it to shut itself down, disposing the browser connections.  It will take some time, but I suspect it might be safer to wait for it to do its thing. Since I'm not really familiar with the native driver, I'm not really sure whether it leaks or not otherwise.

Note: If you run into captcha verifications, just open a new tab in the same browser, go past the captcha challenge, and close that tab. The bot should be able to pick up from there on the original tab.
If, however, you keep getting capthca challenges down the line, it's not worth it. Just disable WalmartBuyer instead.