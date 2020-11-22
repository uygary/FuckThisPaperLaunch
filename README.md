# FuckThisPaperLaunch

Shitty script for purchasing a Ryzen 9 5950X on Amazon.

None of this shit is tested that well really, and I haven't quite touched Python for 2 decades, so you're on your own if things go south.
Keep in mind that it ignores currency, so set your prices and item links carefully.

---

## Populate `.env` file

```
PS D:\CODE\FuckThisPaperLaunch> cp .\.env.sample .\.env
```
Then edit the `.env` file to update these values:
`LOGIN_EMAIL`
`LOGIN_PASSWORD`
`MAX_COST`
`MAX_BUY_COUNT`
Feel free to change the `ITEM_ENDPOINT` setting as well.

## Run

```
PS D:\CODE\FuckThisPaperLaunch> python.exe .\main.py
```
Although I just use PyCharm community edition, even for running this. Ideally you should use `venv` to install the dependencies and run this script.