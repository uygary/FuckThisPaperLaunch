# FuckThisPaperLaunch

Shitty script for purchasing a Ryzen 9 5950X on Amazon.

None of this shit is tested that well really, and I haven't quite touched Python for 2 decades, so you're on your own if things go south.
Keep in mind that it ignores currency, so set your prices and item links carefully.
Since I work with PowerShell, the scripts and these instructions are based on that, but of course you could use any shell you want in order to run this.

---

## Populate `.env` file
This step is necessary only on the first run.


```
PS D:\CODE\FuckThisPaperLaunch> cp .\.env.sample .\.env
```
Then edit the `.env` file to update these values:
`NUMBER_OF_ITEMS` (How many items you're trying to buy.)  
`LOGIN_EMAIL_1`  
`LOGIN_PASSWORD_1`  
`MAX_BUY_COUNT_1`  
`MAX_COST_PER_ITEM_1`  
Feel free to change the `ITEM_ENDPOINT_1` setting as well. There are some example endpoints in the environment file.  
If you have more items to buy, keep editing or adding new entries for each of these configuration values that end with `2`, `3`, etc.

Update the `IS_TEST_RUN` value to `False` when you're happy with the settings.

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