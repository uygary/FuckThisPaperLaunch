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
`LOGIN_EMAIL`
`LOGIN_PASSWORD`
`MAX_COST`
`MAX_BUY_COUNT`
Feel free to change the `ITEM_ENDPOINT` setting as well.

Update the `IS_TEST_RUN` value to `False` when you're happy with the settings.

## Install dependencies
This step is necessary only on the first run.


Open up a PowerShell prompt. (Windows Terminal, ConEmu, or just a PS prompt)
Then run the `init.ps1` script.

```
PS D:\CODE\FuckThisPaperLaunch> .\init.ps1
```
This will basically initialize a virtual environment, activate it, and install dependencies.

## Run
On the same PowerShell prompt just run the `start.ps1` script.

```
PS D:\CODE\FuckThisPaperLaunch> .\start.ps1
```
This will simply run the script.
Of course you could just use PyCharm Community Edition or Visual Studio to run this if you wanna fiddle around with the code and debug it.