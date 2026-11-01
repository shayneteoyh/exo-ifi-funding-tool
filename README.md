# EXO Policy Funding for Indexed Flexi Income

A single-file HTML tool for EXO Advisory Group financial consultants to model
premium financing of an Indexed Flexi Income policy, stress-test FX and
interest-rate moves, and print a client-ready report.

## Usage

Open `index.html` directly in a browser. No build step or server required;
all calculations, PDF parsing and printing run client-side, and nothing is
sent to a server.

Live: https://shayneteoyh.github.io/exo-ifi-funding-tool/

## Margin and FX rates

The iFAST board and preferential margin rates and the units-per-USD FX
rates are refreshed daily at 09:00 Singapore time by
`.github/workflows/update-rates.yml`, which runs `scripts/update_rates.py`
against the feed behind iFAST's public product-financing page and Yahoo
Finance's currency quotes, and commits any change. Run it by hand from the
Actions tab ("Run workflow") or with `python3 scripts/update_rates.py`.
