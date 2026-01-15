# Designing a College Football Playoff Predictor Web Application

## Introduction and Problem Definition

College football fans obsess over rankings, but the only rankings that truly matter are those produced by the College Football Playoff (CFP) Selection Committee. The goal of this project is to build a Python-based web application that emulates the CFP committee's ranking process and allows interactive "what-if" scenario exploration. Users will be able to toggle future game outcomes and immediately see how the committee's weekly Top 25 and playoff selections might change. This is fundamentally different from predicting pollsters or betting odds – it focuses on modeling resume-based evaluation as done by the CFP committee, grounded in historical committee behavior, official criteria, and selection rules.

Key objectives include: (1) understanding how the CFP committee operates and what criteria they emphasize, (2) defining a sensible prediction target for modeling (e.g. rank or selection probability), (3) identifying data sources for game results and past CFP rankings, (4) designing features that mirror committee reasoning (strength of schedule, quality wins, etc.), (5) choosing an appropriate modeling approach (likely a machine learning model for rankings), (6) implementing a fast scenario simulation engine to recompute rankings after hypothetical results, and (7) recommending a suitable tech stack and architecture for a Python-only implementation. Throughout, we will consider project scope, limitations, and how to maintain credibility and transparency in the model's predictions.

## CFP Selection Process & Rules

### Committee Structure and Weekly Rankings

The CFP Selection Committee is a 13-member panel of former coaches, athletes, and administrators that meets weekly during the latter half of the season to produce the official Top 25 rankings. Starting around mid-season (typically the first rankings are released in early November), the committee convenes in person each week to evaluate teams' performances and vote on rankings. The committee has no fixed mathematical formula; instead, they rely on a deliberative voting process and holistic review of teams' résumés. By protocol, they generate the rankings through rounds of ballots, often ranking teams in groups (e.g. first rank 1–4, then 5–8, etc.) to ensure careful consideration of playoff contenders. Committee members must recuse themselves from discussions or votes involving teams with which they have conflicts of interest (such as their former schools or employers), ensuring as impartial a process as possible.

### Selection Criteria

The CFP committee evaluates teams using a set of guiding criteria that are stated in the official protocol. Specifically, when comparing teams, they consider factors such as: win-loss record and overall performance, strength of schedule, head-to-head results, results against common opponents, and whether a team is a conference champion. Other relevant considerations include "game control" or dominance and circumstances like key player injuries that might affect performance. Importantly, there is no rigid weighting or points system for these criteria – it's a subjective assessment where committee members balance these factors as they see fit. For example, an undefeated record or a conference championship can carry significant weight, but a one-loss team might be ranked ahead of an undefeated team if the former played a far tougher schedule or has a head-to-head win over a comparable contender. The committee explicitly avoids metrics that encourage running up the score; margin of victory is not supposed to be incented (they focus on wins and losses, not point spreads). In practice, this means the process has an inherent human element: some aspects of committee behavior (e.g. the "eye test" of how dominant a team looks) are subjective and not directly observable in data.

### The 12-Team Playoff Format

Beginning with the 2024 season, the CFP is expanding from a 4-team playoff to a 12-team playoff field. Under the new format, the selection committee will still rank the Top 25 as usual, but the playoff bids and seeding follow specific rules:

- The field will include the five highest-ranked conference champions (which guarantees that at least five conference champions are in the playoff, even if one falls outside the top 25 rankings) and the next seven highest-ranked teams as at-large selections. This effectively replaces the old "top 4 teams" selection with a broader net of 12 teams, with automatic inclusion of top conference champs.

- The top four seeds in the playoff are reserved for the top four ranked conference champions, each receiving a first-round bye directly into the quarterfinals. These are typically the champions of major conferences (e.g. SEC, Big Ten, etc.) if they rank highly.

- Teams seeded 5 through 12 will play in the first round (the higher seed hosts a home game in the first round: e.g. seed 5 hosts 12, 6 hosts 11, 7 hosts 10, 8 hosts 9). The winners advance to face seeds 1–4 in the quarterfinal bowl games, following a standard bracket structure (No. 1 seed faces the 8/9 winner, No. 2 faces the 7/10 winner, and so on).

- Selection Day (the Sunday after conference championships) is when the final committee rankings and the playoff bracket are released. At that point, if any of the five guaranteed conference champions were not already in the top 12 of the rankings, they will be included by bumping out the lowest at-large team and will be slotted in at the #12 seed (or #11 and #12 if two such champions are outside the initial top 12). This ensures the required representation of conference winners.

- There is no reseeding after any round. The bracket positioning is fixed based on the final seeds – for instance, the #1 seed's path will always face the 8/9 winner in the quarterfinal and then potentially the 4/5/12 group winner in a semifinal, etc., rather than reshuffling to always face the lowest remaining seed.

Under this expanded format, the committee's role is not only to rank teams 1–25 each week, but on Selection Day to ensure the playoff bracket is constructed according to the rules. Notably, a highest-ranked Group of 5 (mid-major) conference champion is guaranteed a spot if it is among the top five conference champs, which could lead to a lower-ranked team being included at the expense of a higher-ranked at-large team just outside the cut. For example, if in a given year the fifth-best conference champion is ranked #20, that team would still get into the playoff (as a #12 seed), displacing the would-be at-large team ranked #12. The committee's final seeding also respects traditional bowl affiliations for quarterfinal placements when possible (e.g. letting an SEC champion go to the Sugar Bowl if it's a quarterfinal host). All these rules need to be accounted for when translating predicted rankings into a playoff bracket in our application logic.

### Observable vs. Subjective Factors

Many inputs to the committee's decisions are based on tangible data – wins and losses, opponent quality, championships won, etc. – which we can model. Indeed, the CFP committee even introduced enhanced statistical metrics in 2025 (like a "record strength" metric to quantify the quality of a team's wins and losses) to better inform their discussions. This new record strength metric essentially rewards teams for beating high-quality opponents and minimizes the penalty for losing to very strong teams, while doing the opposite for games against weak opponents. In other words, it codifies the notion of "quality wins" and "bad losses," which historically the committee has talked about qualitatively. By adding such metrics to their toolbox, the committee is trying to be more data-driven. However, even with more data, the process remains partly subjective – there is no fixed weighting of criteria and no formula that produces the rankings. Committee members may have differing opinions on how much a dominant game or an injured quarterback should matter. Certain aspects, like a team's perceived momentum or how "impressive" a win looked (the famed "eye test"), are not explicitly measured but can influence votes. Our model will aim to capture the observable, resume-based factors (record, schedule strength, head-to-head results, etc.), acknowledging that there is an irreducible subjective element we cannot fully replicate. The goal is to approximate the committee's behavior as closely as possible using data, while understanding that perfect prediction is impossible – even the committee's own logic can evolve year to year.

## Defining a Predictable Target for the Model

One of the first design decisions is choosing what exactly we want our machine learning model to predict. Since we're emulating a ranking process, there are a few plausible target definitions:

### Rank Position (Ordinal 1–25)

We could try to have the model predict a team's exact rank (or whether it's unranked). This is essentially an ordinal classification problem. However, predicting exact ranks 1 through 25 is very challenging – the difference between rank #4 and #5 is critical (playoff cutoff), but the difference between #17 and #18 might be relatively minor. A multi-class classification (with 26 classes if we include "unranked" as a class) would likely be unwieldy and not capture the relative nature of rankings well. There's also no simple "distance" metric between ranks that a typical classifier would understand (is misclassifying a #5 as #6 better or worse than misclassifying #5 as #15?).

### Continuous "Ranking Score"

Another approach is to assign each team a continuous score that corresponds to its standing in the committee's eyes, and have the model predict that score via regression. In practice, we can derive a target score from the historical rankings – for example, one could assign 1.0 for the top-ranked team, 2.0 for the second, ..., 25.0 for the 25th, and perhaps 30.0 for any team outside the Top 25 (or some constant for "unranked"). The model then outputs a real-valued "rank score," and by sorting teams by this predicted score we can produce a full ranking. This treats the ranking problem as a regression where lower score = better team. It has the advantage of naturally handling the ordering – the model's job is to learn a scoring function that, when sorted, recreates the committee's ordering of teams. Many successful ranking prediction systems use this kind of approach. Essentially, we're training the model to imitate the underlying rating that the committee implicitly gives teams. This was indeed the strategy used in at least one research model, where a linear regression was trained on committee decisions and "utilizes quantities from [a] power rating system to generate an ordering for all teams", successfully matching the committee's top four selections with high accuracy. By treating rank as a continuous outcome, the model can express "how strong is this team's résumé" on a spectrum, which is more informative than a hard class label.

### Probability of Selection/Playoff (Binary classification)

We could simplify the problem to predicting the probability that a team makes the playoff (or is ranked in the Top N). For example, a classifier could be trained to predict whether a team will be in the top 4 (in the old format) or top 12 (in the new format) – essentially a yes/no prediction for playoff inclusion. This might be easier in some respects (binary classification), and it is indeed something the committee's data analysts and others have done (e.g. producing playoff odds for teams). However, this approach doesn't give a full ranking of all teams, just the set of who's in or out. Since our application aims to show the whole ranked list and not just the playoff cut line, a binary prediction is too limited. It could be a secondary output (e.g. "Team X has a Y% chance to be selected"), but it doesn't solve the core ranking problem.

### Chosen Approach: Continuous Ranking Score

Given these options, the most flexible and "committee-like" target is to use a continuous ranking score that can be derived from historical rankings. We will treat each team's weekly ranking as a data point. For teams ranked 1 through 25 by the committee in a given week, their target score can be their rank (1 = best). For teams outside the top 25 that week, we can assign a neutral placeholder (e.g. 30, or 26 – something slightly worse than the last ranked team) as their target. This way, the model can be trained on all teams, not just the ranked ones, and it learns to give higher scores (lower numeric value) to teams the committee tended to rank, and lower scores (higher value) to teams they did not. In essence, the model is doing a form of ordinal regression, even if we train it as a standard regression problem. By sorting the model's predictions, we can generate a full ranking and identify which teams would be top 4, top 12, etc. This approach has been validated by prior work – for instance, a simple linear regression model using resume metrics was able to correctly predict 84% of the committee's top-four selections over several years, indicating that mapping team data to a continuous score can work well.

Another nuance is how to handle the weekly aspect. The committee issues a new ranking each week based on games up to that point. Therefore, our training data will consist of multiple snapshots per season (every week the committee published rankings). For each snapshot, we use the data available up to that week and the committee's ranking that week as the target. We must ensure our model doesn't "peek" at future results. For example, when predicting the Week 10 rankings of 2022, the features for each team should only reflect games through Week 10 of 2022. By structuring the data this way, the model learns the relationship between a team's resume at a given time and the committee's evaluation at that time. Historical committee rankings (2014–present) are published and can be compiled into a dataset – each team either has a rank 1–25 or is unranked in each week's list. We will convert those into numerical targets as described.

In summary, we will train a regression model to predict a "committee ranking score" for each team-week. This score, when sorted, yields the predicted ranking order (lower score = higher rank). From that, any downstream outcome (like "makes playoff or not") can be derived by looking at the top 4 or top 12 teams in the predicted ranking. This strategy is both defensible and practical: it aligns with how power ratings or indices can be used to sort teams, and it provides more information than a binary classification. It also handles the fact that the committee's output is an ordering, which is fundamentally what we care about emulating.

## Data Feasibility & Sources

Building this system requires several categories of data:

### Historical Committee Rankings

We need the week-by-week CFP rankings for past seasons (from 2014, when the CFP began, through the present). Fortunately, these are publicly available. The official College Football Playoff site publishes each week's Top 25 rankings (and has archives for all years). These can be scraped or manually compiled. Additionally, websites like Wikipedia often summarize the final CFP rankings of each year, and some data repositories include weekly poll data. A particularly convenient source is the CollegeFootballData (CFBD) API, which provides programmatic access to historical poll rankings, including the CFP committee poll. The CFBD API offers clean, structured data for college football, so one can retrieve the CFP Top 25 for each week of each season through a simple query (with an API key). Using an API avoids manual scraping and ensures consistency.

### Game Results and Team Schedules

To evaluate team résumés, we need detailed regular season results: wins, losses, opponents, game dates, and possibly scores. This data can be sourced from the CFBD API as well, which includes game results for all teams and seasons. Another source is sports-reference.com's College Football section or ESPN's data, but CFBD provides it in a ready-to-use JSON/CSV format via API. We will gather all games from 2014–present, including the scores and which week they were played (or at least the date, which we can map to week number). Team schedules can be derived from the game results by filtering by team.

### Team Metadata (Conferences, etc.)

Since conference championships and conference strength matter, we need to know which conference each team was in each year, and which team won each conference. Conference realignment has occurred (for example, Texas A&M moved to the SEC earlier, and starting in 2024 many teams are switching conferences), so it's important to use year-specific team–conference mappings. CFBD provides team info and conference info by year, as well as listings of conference championship games and winners. Alternatively, this can be manually maintained for major conferences. We also might want to flag teams as "Power Five" vs "Group of Five" for each year (in 2014–2023, the Power Five conferences were ACC, Big Ten, Big 12, Pac-12, SEC; in 2024, the labels might shift with realignment but concept remains).

### Derived Data – Weekly Team Records and Stats

We will need to compute each team's record at each relevant week (e.g. going into the committee ranking, Team A is 9–1, Team B is 10–0, etc.), as well as their strength of schedule and other features. This means aligning games to the timing of rankings. Typically, the committee's Week N ranking includes games through that weekend's action (released on Tuesday of the next week). For instance, the first CFP ranking might come after Week 9's games. We should confirm the timeline each year (the CFP site's ranking schedule confirms the dates). Aligning is straightforward: for each ranking release, consider all games up to the preceding Saturday. We also handle bye weeks (teams with no game still have the same record as previous week). The challenge is that teams not in the Top 25 won't be listed by the committee, but we need to include them in our dataset as having a not-ranked status. We can assume any FBS team not listed is effectively "ranked" 26th or worse. In practice, we might include all teams with at least a winning record or all FBS teams in the dataset for completeness, marking most as unranked.

### Key Data Challenges

**Teams dropping in/out of Top 25**: The composition of the ranked teams changes weekly. A team might be unranked one week and then ranked the next after a big win. When building training data, we should include those unranked cases as well so the model learns what an unranked resume looks like vs. a ranked one.

**Limited data points per season**: The committee releases about 6-7 weekly rankings per year (including the final one). That means ~60-70 total ranking snapshots from 2014–2023. However, by treating each team in each snapshot as a separate sample, we actually have thousands of training examples (roughly number of teams * number of weeks per season).

**Conference realignment and format changes**: Our historical data covers the 4-team playoff era (2014–2023). Starting 2024, the playoff expands to 12 teams, but importantly the committee's ranking process and criteria remain largely the same – they will still rank 25 teams each week. The difference is in how the playoff teams are picked from the ranking. Our model can still be trained on the 2014–2023 data (where top 4 was the playoff) because the way the committee ranks teams 1–25 shouldn't drastically change. We just have to be mindful that in 2024+ the incentive structure changes a bit (e.g. being #12 vs #13 now matters a lot more). We might address this by giving slightly more attention to those cutoff regions in evaluation. Conference realignment means some features (like "Power Five conference") need to be dynamic by year. For example, in the future the Pac-12 is dissolving, so "Power Five" might effectively become Power Four, etc. But historically, we label teams according to the landscape of that season.

**Data availability**: All the needed data (scores, rankings, etc.) are publicly accessible. The CFBD API in particular is a one-stop shop for game results, team stats, and polls. Using it ensures our data pipeline is reproducible and up-to-date. If CFBD didn't have something, alternatives include scraping official releases or using Kaggle datasets that some users have compiled for past seasons. We will also keep an eye on data quality (e.g. consistent team naming, handling of FBS vs FCS games for schedule strength, etc.) with a data validation step.

In summary, data feasibility is high: we have about a decade of CFP committee decisions and extensive game data to learn from. The project will involve writing a data pipeline to fetch and aggregate: all FBS games results (winners, scores, dates), team info (conference membership each year), and weekly CFP rankings (team and rank for each week). We will then process this into a structured dataset of team-week records with the features and target (committee rank or score). Given that CFBD provides most of this via API, we can automate data collection. The data pipeline will also need to compute certain metrics (like strength of schedule) that aren't directly given but can be derived from the raw results.

## Feature Engineering for "Committee-Like" Evaluation

To predict the committee's rankings, our model needs to look at teams the way the committee does – essentially, mimicking a human résumé evaluation. We will design features that capture the key criteria and common discussion points used in committee evaluations:

### Win–Loss Record

At its core, a team's record is the first line of the résumé. We will include features for total wins, total losses, and win percentage up to that week. Since not all 10–2 records are equal, we'll go further, but a team's record sets the baseline (undefeated teams are always ranked highly, one-loss teams next, etc., barring extraordinary circumstances). We might break down wins by type: e.g. conference wins vs non-conference wins (since committee members often note if a team dominated its conference or struggled out of conference).

### Strength of Schedule (SOS)

This is explicitly mentioned as a major factor. We will quantify SOS in a couple of ways. A simple metric is the average win percentage of a team's opponents, or perhaps a weighted version accounting for whether games were home/away. We can also compute a team's SOS rank (i.e. rank teams 1–130 by the difficulty of their schedule so far). The committee now uses an enhanced metric that gives more weight to games against strong opponents. In practice, that suggests our SOS should emphasize if you played many ranked or winning teams. We could include a feature like "number of opponents faced who are currently (or ended season) above .500 (winning record)" as a proxy. Our model might also incorporate an external strength rating – for instance, ESPN's Strength of Record (SOR) or Strength of Schedule indices if available, or we can compute something similar. According to ESPN, the "record strength" metric they gave the committee "rewards those that beat high-quality opponents while minimizing the penalty of losing to one… and imposes a greater penalty for losing to [lower-quality opponents]". We can mirror this by counting "quality wins" and "bad losses", described next.

### Quality Wins & Bad Losses

These resume bullet points often come up in debates. A "quality win" typically means a win against a highly regarded team. We will include features such as:

**Wins vs Ranked Teams**: How many wins does the team have against teams that are (or were) ranked? We have to decide whether to use opponent's ranking at game time or opponent's current standing. The committee tends to evaluate wins in hindsight (e.g. "Team A beat Team B, and Team B is now ranked #15 – that's a quality win"). We could use the previous week's CFP rankings to identify which opponents were Top 25 at the time. Or use the final rankings for end-of-year evaluation. We might have a feature for "wins vs CFP Top 25 teams (at time of playing or at present)."

**Wins vs Winning Teams**: Number of wins against opponents with winning records (above .500). This captures quality in a broader sense – beating a bunch of 3–9 teams isn't impressive even if your record is 10–2. Committee statements often mention if a team "beat X teams with winning records."

**Power 5 Wins**: Number of wins against "Power Five" conference teams. Beating teams from the stronger conferences is generally valued more than piling wins against smaller programs. For Group of Five teams, their lack of Power 5 wins often hurts them.

**Bad losses**: We will flag if a team lost to a weak opponent. For example, a feature for "losses to teams with losing records" (sub-.500 teams). A single bad loss can severely damage a team's ranking. Conversely, losing only to top teams might be seen as more forgivable. We can also record "losses to Top 10 teams," which might be seen as quasi-acceptable (e.g. losing to the #1 team by 3 points might not drop you much). Essentially, we separate losses into "good losses" (to strong teams) and "bad losses" (to weak teams) to allow the model to penalize them differently.

### Score margins (used cautiously)

While the committee says they don't incentivize margin of victory, they do get game control metrics and will notice if a team barely wins vs dominates. We might include a subtle feature like average point differential or points per game vs points allowed, to hint at team dominance. But we must be careful since the committee explicitly avoids using MOV in comparisons. Any such feature would be a minor one, used cautiously, just in case it helps the model distinguish, say, a team that consistently wins by 30 (likely very strong) from one that squeaks by inferior opponents.

### Head-to-Head and Common Opponents

These criteria are tricky to encode directly because they are relational – they involve comparing two specific teams. The committee uses head-to-head results as a tiebreaker, essentially, if teams are otherwise comparable. For modeling, one way to partially capture this is:

If Team A beat Team B, and our model is considering ranking, it should ideally rank A above B if their resumes are otherwise similar. We can't explicitly input "Team A beat Team B" for every possible pair (that would explode the feature set). But we can incorporate it implicitly: features like quality wins already count beating good teams. So if A beat B and B is a good team, A's quality-win count goes up. We might also include a feature like "has head-to-head win over any team with equal or better record" to identify when a team has a direct win that could boost them.

**Common opponents**: similarly, this is hard to encode generally. It might be beyond our scope to handle every pairwise comparison the committee could draw. But by capturing overall performance and schedule, we indirectly cover many common opponent scenarios (e.g. if Team A struggled against a team Team B beat easily, that might reflect in point differential, etc., which we minimally incorporate).

### Conference Champion Status

The CFP protocol explicitly gives weight to winning one's conference, especially when comparing similar teams. By Selection Day, being a conference champion can elevate a team's ranking (e.g. a 11–2 conference champion might leapfrog a 11–1 non-champion if they were close). We will include a binary feature for "conference champion" (for the final ranking week) and perhaps for interim weeks something like "controls destiny for conference championship" or simply the current conference standing. However, until championship games are played, this is not resolved. For simplicity, for interim weeks we might include whether the team is leading its division or has clinched a title game berth (but that may be too detailed). At minimum, in the final-week data, mark the champs. In a what-if scenario, once the user chooses winners of title games, we can set this flag accordingly.

Additionally, include a feature for conference affiliation (perhaps as categorical). The model might learn different baselines for teams in SEC vs Sun Belt, etc., reflecting that a 10–2 SEC team is viewed differently from a 10–2 team in a weaker conference. There is some risk here – we don't want to hard-code bias, but historically it's true the Power Five conference teams dominate the rankings. We can represent conference by a one-hot encoding or a flag for Power Five vs Group of Five. This helps the model know, for example, an undefeated Mountain West team might still rank behind a one-loss SEC team (as has happened).

### Momentum/Recency

Humans often consider "how is the team playing lately." While the committee insists every week is a fresh evaluation, they are not immune to recency bias. We can try to capture momentum with features like:

- Current win streak length.
- Whether the team won its most recent game (almost always yes for teams moving up, except bye weeks).
- Quality of recent opponents: e.g. if in the last 3 games the team beat two ranked opponents, that could boost their ranking significantly.

These features might help in scenarios where a team started poorly but has since gotten big wins (the model might otherwise undervalue them based on full-season averages). However, we should be careful that these don't leak future info – they must be computed up to that week only. For example, if by week 10 a team is on a 4-game win streak, that's fine to include.

### External Ratings (optional)

We face a trade-off: we want to ground everything in "committee-like" reasoning, not just generic power ratings. However, sometimes incorporating an external metric as a feature can improve accuracy. For example, including the team's Elo rating or FPI (Football Power Index) or SP+ could give the model some sense of team strength beyond wins and losses. The danger is that some power metrics heavily use margin of victory or preseason priors, which the committee may not align with. In fact, studies have shown that ESPN's FPI would have mispredicted several committee choices – e.g., FPI infamously thought 13–0 Florida State (2014) was only the 10th best team, but the committee still ranked them #3 due to being undefeated. If our model relied too much on FPI, it might undervalue such teams. On the other hand, a metric like "strength of record" (SOR) is specifically designed to reflect resume quality (it asks: given the team's schedule, what is the probability an average top-25 team would have this record or better?). SOR is actually something the committee now looks at. If available from a source, SOR could be included or we can compute a simplified version ourselves.

In our design, we choose to include an Elo rating as a feature but use it carefully. Elo (if calibrated to CFB) can serve as a summary of team strength accounting for all games and scores, but we will treat it as just one of many features. The model can decide how much to use it. Elo can help break ties between teams with identical records by giving a sense of which team's wins were more convincing overall.

We will not rely on any single external ranking as the output, since that would defeat the purpose of learning committee behavior. Instead, every feature – whether wins, schedule, or an advanced stat – is provided to the ML model, and it will learn the best combination. If the committee historically favored record over efficiency metrics, the model will learn that from examples like the FSU case (where FSU's perfect record outweighed their mediocre power rating).

In summary, our feature set is designed to mirror the criteria and language used by the committee:

- **Record**: wins, losses, win% (overall and conference).
- **Quality of wins**: count of wins vs good teams (ranked or winning record, etc.).
- **Quality of losses**: indicators for bad losses or lack thereof.
- **Schedule strength**: opponent win% and/or rank of schedule difficulty.
- **Contextual factors**: conference champ status, Power5 vs Group5, etc.
- **Recency**: streaks and last game result.
- **Miscellaneous stats**: scoring margin, offensive/defensive ranks (if needed, but minimal).
- **Derived metrics**: possibly an overall resume score or power rating (Elo, SOR).

All features are computed per team per week using data available up to that week. For example, to compute Team X's features for the Week 12 ranking of 2023, we look at all games Team X played through Week 12 and all opponents' records through Week 12, etc. This ensures the model is always using the same information the committee had at that time.

As a concrete example, consider a team that is 10–2 at end of the season: Let's say they have 3 wins over teams that finished in the CFP Top 25 (quality wins), and one of their losses was to a team with a losing record (bad loss). They also won their conference championship. Our features would encode: Wins=10, Losses=2, win% ~0.833; quality_wins=3; bad_losses=1; conf_champ=1; opponent_win_pct (maybe 0.600, if their opponents on average went 7-5); perhaps Power5=1 (if applicable); last5_games_won=5 (if on a 5-game streak through the championship). We feed those into the model, and ideally it would output a score ranking them around where the committee would (which might be, say, rank 7 if those numbers are impressive).

We should also highlight how our features align with what the committee explicitly said it values. The committee's own "evaluation criteria" list (from an official CFP guide) includes Strength of Schedule, Conference Championships, Head-to-Head, Common Opponents, Overall Performance. Our features cover each of these:

- **Strength of schedule** → opponent win% and quality metrics.
- **Conference championship** → explicit feature.
- **Head-to-head** → implicitly in quality wins (if head-to-head was against a good team) and can be handled in scenario logic if needed.
- **Common opponents** → indirectly via overall performance stats.
- **Overall performance** → captured by wins/losses and scoring margins.

By engineering features in this way, we give our model the inputs to act "like a committee member." We also maintain transparency – each feature has a clear interpretation (we can explain to users what factors influenced the model's output, e.g. "Team A is ranked above Team B because it has more top-25 wins and a tougher schedule, even though both have one loss").

## Modeling Approach and Validation

With data and features in hand, we need to choose a modeling technique that suits this problem. This is a classic tabular data prediction task with a twist: the target is an ordinal ranking outcome. For such tasks, ensemble tree-based models (like Random Forest or Gradient Boosting Machines) are often very effective. We will use a gradient boosting regression model (XGBoost) to predict the committee's ranking score for each team-week. There are several reasons why XGBoost (Extreme Gradient Boosting) is a good choice:

### Why XGBoost?

**Handles Non-Linearity**: The relationship between features and rank is not linear. For example, going from 0 losses to 1 loss can drop a team significantly in rank (especially late in the season), but going from 3 losses to 4 losses might not change their rank much (they're likely out of contention either way). A tree-based model can naturally handle such non-linear effects (it can learn different rules in different ranges of data).

**Feature Interactions**: The importance of a feature can depend on another. Being undefeated in the SEC is different from being undefeated in a smaller conference – the model might need to combine "losses = 0" with "Power5 status" to properly rank teams. Decision trees will consider such interactions. For instance, it might learn a rule "if team is Power Five and losses=0, then extremely low rank score (i.e. likely top 4)". These conditional relationships are hard to capture with a simple linear model without manually adding interaction terms.

**Robust with Many Features**: We plan ~30+ features, and gradient boosting can handle that dimensionality well, picking the most informative ones and ignoring irrelevant ones.

**Handles Categorical Vars**: XGBoost can work with one-hot encoded conferences or similar categorical data effectively, splitting on those as needed.

**Small Dataset Friendly**: Our dataset, though spanning a decade, is not huge in rows (tens of thousands of team-weeks). XGBoost is well-suited to smaller datasets and less prone to overfitting than a deep neural network would be, given this data size.

**Interpretability**: We can extract feature importance scores to see which factors the model is relying on, which helps ensure it aligns with known committee criteria. We could even use SHAP values or partial dependence plots to explain to users which aspects of a team's resume boosted or hurt its ranking – supporting transparency.

We will treat the problem as a regression: the model outputs a continuous score for each team-week. During training, the loss function pushes those outputs to match the target ranking scores we assigned (where, say, Alabama week 15 2020 should output ~1.0 if they were ranked #1, etc.). During prediction/inference, we will take all teams in a given week scenario, predict scores, and then sort by score ascending to get the ranking.

### Model Training

To train the model, we'll gather all historical snapshots (2014–2023). We will likely split the data into a training set and a validation set by season (to evaluate performance on seasons the model hasn't seen). For example, train on 2014–2020 data and validate on 2021–2023. This temporal split is important – we want to simulate how the model would perform on future seasons, not just random train-test splits from the same years (which could leak some year-specific patterns). Using earlier seasons to predict later seasons tests generalization. We also ensure that for any given season in training, we don't train on data from after the week we're predicting (the way we construct data already ensures that).

We'll tune hyperparameters for XGBoost (e.g. tree depth, learning rate) using the training set, possibly via cross-validation (ensuring folds don't mix seasons). Likely a small tree depth (like 5 or 6) and around 100–200 trees is sufficient given the size of data. We also must be careful to avoid overfitting, since the number of seasons is small and committee behavior could shift. Techniques like early stopping on the validation set or using minimal necessary complexity will be applied.

### Model Validation and Evaluation Metrics

How do we know if our model is any good at reflecting committee rankings? We will evaluate it on historical data (seasons not used in training, e.g. the last few seasons as a test set). Several metrics are useful:

**Rank Correlation**: We can compute Kendall's Tau or Spearman's rho between the model's predicted ranking and the actual committee ranking for each week. These measure how well the ordering is preserved (Tau focuses on pairwise order agreements, Spearman on overall correlation of ranks). A higher correlation means the model's ordering is closer to the true ordering. In initial tests, we might see moderate correlations – any single week's ranking has some noise, but across many weeks a good model should have a positive correlation.

**Top-N Accuracy**: We will specifically check Top-4 accuracy (did the model correctly identify the four playoff teams?) and Top-12 accuracy (under the new system, did it get which teams should be in top 12) as key metrics. These are crucial because getting the playoff field right is more important than, say, distinguishing #20 vs #21. If our model can consistently pick out the semifinalists/top teams, that's a big success. For example, if in a validation season, the actual top 4 were Georgia, Michigan, Oregon, Clemson, we check if those four are the top 4 in our predicted ranking (order can be different, or even if order is different we might consider it partially correct if the set matches). The user-provided summary suggests a target of 100% top-4 accuracy on validation, which means the model perfectly identified all playoff teams in the test years. That is an ambitious target but not impossible if those seasons were somewhat straightforward.

**Mean Rank Error**: We can average the absolute difference between a team's predicted rank and actual rank, for teams in the Top 25. This gives a sense of how far off the model typically is. If the mean error is, say, 3 positions, that's pretty good; if it's 10, that's poor. We might find the model is very accurate at the top (where data signals are strong: record, etc.) but less so in the middle of the rankings where many teams have similar profiles.

During validation, we will also examine specific cases:

Does the model occasionally rank a team much higher or lower than the committee did? If so, why? We might find a case like 2018 UCF (undefeated non-power team) where the model could either overrate them (because 12–0 record) or underrate them (because of weak schedule) relative to committee. Those insights can guide feature adjustments or at least be noted as limitations.

If the model shows it can reproduce committee rankings closely (e.g. often the same top 4, and high correlation on ordering), then we have evidence it "meaningfully reflects committee behavior." An example result could be: Kendall's Tau ~0.1–0.2 (which is moderate for a 25-length ranking), Top-4 accuracy 90%+, Top-25 membership accuracy 80% (meaning 80% of the teams it predicts to be ranked are actually ranked, indicating it rarely misses a team or includes a wrong team). In one hypothetical experiment, a model achieved 83% Top-25 accuracy and perfectly identified all top-4 teams in the test set. However, its exact ordering had only a weak correlation (Tau ~0.06–0.11), reflecting that while it knows who should be in the playoff, it might not place every team in the exact committee order. This is acceptable because our primary aim is to capture the major outcomes (who's in playoff, who's top 10 etc.), not necessarily whether Team #18 and #19 might be swapped.

We will also do case studies on the validation set: e.g. 2023 final ranking – check how the model handled the controversy of Florida State vs Alabama (FSU was 13-0 but lost its QB, Alabama 12-1 with big wins). Our model's features might not capture "lost star QB" explicitly, so it might rank FSU higher than the committee did. Recognizing such a limitation is important; we might note that the committee applied the "key player availability" criterion in that case which our data didn't capture. These kinds of edge cases will be documented as scenarios the model might not predict "correctly" because they hinge on subjective factors not in our data.

**Algorithm alternatives**: We considered other approaches like training a pairwise ranking model (e.g. using an SVM-rank or neural network that learns to say "Team A should be ranked above Team B") or a deep learning model that could take raw data (maybe a network that processes team schedules as a sequence). Those are interesting, but given the size of data and need for interpretability, they are likely unnecessary. A pairwise approach would massively increase the training sample count (we'd generate comparisons between many team pairs) and complicate training, while a straightforward regression on an absolute ranking score is easier and works well. Neural networks could fit the data too, but with only ~10 seasons, a complex network might overfit and would be a black box in terms of explaining why it ranks teams a certain way. The current approach using XGBoost gives us a good balance of performance and explainability, and tree-based models have been successful in many sports analytics contexts (they often win Kaggle competitions for tabular sports data predictions).

In training, we'll also perform feature importance analysis. If the model is truly emulating the committee, we expect features like wins, losses, schedule strength, quality wins to be top contributors. If we find something odd (e.g. if an Elo feature dominated and made the model act more like a power rating than a resume evaluator), we might reconsider that feature's inclusion or weight. The modeling process is thus iterative: generate features, train model, evaluate against known committee decisions, and adjust.

Finally, to ensure the model doesn't just memorize year-specific quirks, we avoid using things like preseason rankings or team name as features – those would cause overfitting (the committee doesn't explicitly consider brand names or preseason rank, at least not overtly). We also keep the time-based split to emulate prediction on new data. If possible, we might even test on 2024 data once a few weeks of the new season are in, to verify performance in the wild (though the expanded playoff might slightly change dynamics, it's still a good test).

## Scenario Simulation Engine ("What-If" Analysis)

A core feature of the application is the ability for users to alter future or hypothetical game outcomes and immediately see the impact on rankings and playoff selection. Building this "what-if" simulation engine involves propagating changes in game results through the data and model:

### User Input – Selecting Outcomes

The user interface will present upcoming games (and potentially even past games, if the user wants to retroactively change a result) and allow the user to pick winners. For instance, a user could say "What if Team A upsets Team B next week?" or even set an entire scenario like "What if Alabama wins the SEC Championship, Oregon loses the Pac-12 Championship, and Texas wins out?" The interface might be a list of games with toggles or dropdowns to select the winner for each. For ease, we might focus on the remaining games of the season (in real time) or for a retrospective scenario, allow selection of any key games.

### Updating Game Results

Once the user makes their picks, the backend will modify the game results dataset accordingly. For any game the user changed, we flip the winner and loser (and could adjust the score, though for our purposes, only win/loss typically matters unless we track score margin features). For example, if the user says Team A beats Team B instead of the actual result, we change that game's outcome in our data structure. This step is straightforward updates to the DataFrame or database of games.

### Recomputing Team Records and Features

With the new results in place, we recalculate all the features we discussed for the affected teams – essentially, we generate a new "world" of data reflecting the hypothetical scenario. This involves:

**Recompute standings and records**: Every team's wins and losses may need updating if their game outcomes changed. If only a few games changed, many teams' records stay the same, but the ones involved in those games (and their opponents, etc.) will change.

**Recompute strength of schedule and opponent info**: If Team A now wins instead of Team B, Team A's record improves and Team B's worsens; all opponents of Team A and Team B now have different opponent win percentages (for SOS) because A's win count and B's win count changed. So, SOS features for teams that played A or B might shift slightly. In principle, a single game's flip can send ripples through SOS calculations for many teams (though minor if their schedules are large).

**Update quality wins/bad losses**: For example, if a previously unbeaten top-ranked team picks up a hypothetical loss in the scenario, that is a significant change for them (no longer undefeated) and a huge quality win for whoever we gave the win to. Conversely, the team that hypothetically loses might drop out of Top 25 contention, affecting who counts as a "quality win" for others. We may need to do an iterative approach: initially, we might guess which teams are ranked to identify quality-win counts, but since that's what we're trying to predict, we might use either the previous week's actual rankings as a proxy or do an initial model run to identify likely ranked teams in the scenario and then refine. However, for simplicity, we can continue using prior info (e.g. if in reality Team B was ranked, and we now gave them a loss, they might drop out, but we won't know until we run the model – a slight circular dependency. A practical solution: just compute quality wins by counting wins over teams that were ranked in the last real ranking or have high Elo, as a reasonable approximation).

**Conference champions**: If we're at the end of the season or including championship games, determine the conference champion in the scenario for each conference. This might require simulating conference standings if multiple teams tie, but since the user likely provides winners of championship games, we can take those directly (for conferences with title games). For conferences that don't have a title game (or if we allow altering a regular season result that determines division titles), we might have to apply tiebreaker logic. For MVP scope, we assume scenarios revolve around obvious changes (like who wins a known matchup).

We recalc all features for all teams or at least all teams in contention. Given the number of teams (130), a full recomputation is not too heavy. Each feature calculation is O(number of teams + number of games), which is fine. To be safe, we can simply re-run our feature engineering pipeline on the modified data to get a fresh feature matrix for the model in the scenario.

### Generate New Rankings with the Model

We then feed each team's updated feature vector into the trained ML model to get a predicted ranking score. This gives us a new sorted order of teams under the scenario. Essentially, we ask the model: "Given this alternate universe of results, how would the committee rank teams now?" The model should output higher scores for teams that benefited from the scenario (e.g. a team that scored a hypothetical big win might jump up) and lower scores for those that took a hypothetical loss.

### Determine Playoff Selection and Seeding

From the new ranking, we apply the CFP selection rules to pick the playoff teams:

- Identify the top 25 teams (the model might rank all 130, but we only present the top 25 as the committee would).
- Among those, note the top five conference champions (using the flags we set for conf champs). Ensure they are all in the top 12 of the bracket; if one is ranked, say, 18th by the model but is a conference champion that needs an auto-bid, we will include that team in the playoff field (by rule) and effectively bump out the lowest at-large team.
- Then seed the 12 teams: the top four champs get seeds 1–4 (ordered by their ranking among themselves), the rest seeded 5–12 by rank. We must be careful to implement the rule that if a champion from outside top 12 gets in, they automatically go to the #12 seed spot.

This yields a bracket: e.g., "Semifinal byes: Georgia (SEC champ), Michigan (Big Ten champ), Clemson (ACC champ), Oklahoma (Big 12 champ); First-round matchups: #12 Tulane (AAC champ) at #5 Ohio State, etc." The logic follows what we described in the CFP format section.

We will present to the user the predicted Top 25 rankings (which they can compare to the current or actual ones) and the predicted playoff bracket in the scenario.

### Efficiency Considerations

The simulation as described recalculates quite a lot, but in practice it's still fast. Recomputing features for ~130 teams over ~12 weeks of games is trivial for a computer. The model prediction for 130 teams is instantaneous (milliseconds). So even if a user toggles multiple scenarios, we can compute each on the fly. If needed, we could cache intermediate results – for example, if a user toggles one game on and off repeatedly, we might reuse some calculations – but it's likely unnecessary. Each "Run Simulation" action will just trigger a recompute. We should ensure that the data updates are reversible or based on a copy of the dataset, so that one scenario doesn't permanently alter the baseline data for the next scenario (unless we explicitly allow sequential scenario building). The safest approach is: always start from the actual season data as baseline, apply the user's hypothetical changes to create a modified copy, run the pipeline, then discard it when done (or keep it until the next run).

A step-by-step illustration of the simulation process is as follows:

1. User selects scenario: e.g., they pick winners for the SEC Championship, Big Ten Championship, etc., in the app.
2. Update data: Mark those selected teams as winners in those games, adjust win-loss for teams involved.
3. Recompute all features: now Team X might have one more win, Team Y one more loss, etc. Recompute their quality wins, new conference champs, etc., reflecting the user's scenario.
4. Model predicts new ranking: The trained XGBoost model produces a new ranking score for each team, based on the new features.
5. Sort and select playoff: Identify top teams and apply 12-team selection criteria (guarantee top 5 champs, seed them accordingly).
6. Display results: Show the user something like "Projected CFP Top 25 Rankings" and a bracket of first-round and quarterfinal matchups given their scenario.

The scenario engine essentially runs the same computations as used in training/initial prediction, just on different input data. This highlights the importance of a clean separation between: the data/feature pipeline (which given any set of game results can produce the features and identify champs), the model prediction, and the selection/bracket logic. We will implement the simulation such that it leverages these components modularly.

One challenge in what-if scenarios is when a user wants to explore many games. If they flip half the season's results, the scenario is drastically different – but our system can handle it as just another input. If they flip just one game, it's a slight perturbation – we should ensure even small changes recalc properly (no shortcuts that assume one game change doesn't affect others, because it can via SOS).

Another aspect is user guidance: We might highlight to the user which games are most impactful. For example, upsets in championship games or late-season ranked matchups will have large effects. The UI could prioritize listing those for toggling. But that's a bonus; at minimum, the user can choose from all upcoming games.

Lastly, testing the engine on known scenarios is crucial. We can validate the simulation by feeding actual results and seeing if it reproduces the actual committee ranking. For example, take the actual Week 15 of 2023 data and run it through the model – it should output something close to the actual final ranking. If it does, then if we tweak a result (say flip one game's winner), we trust the changes in output are meaningful.

In conclusion, the "what-if" engine will allow dynamic exploration. Technically, it's like running a mini-season simulation: you change outcomes and instantly get a new "final ranking". This is powerful for users (e.g., "If these 3 favorites all lose next Saturday, here's how the playoff might shake out"). Ensuring this is fast and accurate will be a key part of the project's success.

## System Architecture and Tech Stack Considerations

Building this project in Python, we have several components that need to work together. A clean separation of concerns will make the system more maintainable:

### Data Ingestion & Processing (Pipeline)

This part (possibly a module `src/data/`) will handle retrieving data (from CFBD API or other sources) and preparing it for use. It involves fetching games, rankings, etc., then computing the features for every team-week. This can be done as an offline batch process (for training the model) and also can be reused for the scenario simulation (for recomputing features on the fly). We will likely build functions or classes that given a dataset of games, produce a dataframe of features. Using pandas and possibly some SQL or direct API calls in Python is suitable. We'll also include data validation steps – e.g., ensuring no games are missing, records consistency, etc. The data pipeline can be run periodically to update the model with new seasons as they complete.

### Model Training (Model module)

We will use libraries like XGBoost (xgboost Python package) or possibly scikit-learn's GradientBoostingRegressor for the ML model. XGBoost has Python bindings and is quite fast. Training can be done in a Jupyter notebook or a Python script, and the resulting model (which is basically a set of trees) can be saved to disk (using XGBoost's model save or pickle) to be loaded by the web app for predictions. We may also consider using scikit-learn for easier pipeline integration, but XGBoost's API is fine. The model code will include hyperparameter tuning (could use scikit-learn's RandomizedSearchCV or just manual tuning given the dataset size). After training, we will have a fitted model that maps our feature vector to a ranking score.

### Web Application (UI module)

The interactive front-end will likely be built with a Python web framework. Given the requirements (rapid prototyping, all Python implementation, interactive sliders/dropdowns for games), a great choice is Streamlit or Plotly Dash. These allow you to create web apps in pure Python, with UI components bound to Python functions. Streamlit in particular is very straightforward: you write a script that defines the widgets and what happens when they change. It can display dataframes, charts, and text easily. For this project, Streamlit could provide:

- A "Game Selector" page where upcoming games are listed with controls to pick winners.
- A button to run the simulation.
- A "Projected Rankings" page that, after simulation, shows the top 25 teams in order, perhaps with their predicted rank score and key resume info.
- A "Playoff Bracket" page that visualizes the 12-team bracket (which we can generate as text or maybe a simple plotted bracket graphic).

Streamlit will handle the user interactions and can call our simulation engine function under the hood. The main downside of Streamlit is that it's less customizable in design, but for an internal or demo tool, it's great. Dash could be used if we needed more flexible layouts or persistent callbacks, but it requires more setup.

Another approach is a traditional Flask or FastAPI backend with a JavaScript frontend (React, etc.), but that's likely overkill for an MVP and introduces complexity (and requires writing JS). Since the user specifically said "Python-only implementation" and is focusing on research and correctness over fancy UI, Streamlit fits well. It allows quick development and even embedding plots (maybe we can plot the ranking over time or scenario comparisons).

We should also consider deployment: Streamlit apps can be hosted easily on Streamlit sharing or other platforms, as long as the data and model are included. If we use Flask, we'd need to host the web service and possibly the model as an API. Given our interactive "what-if" need, a live app with immediate feedback is ideal – that's exactly Streamlit's use case.

### Connecting it Together

The web app will load the trained model (from file) and have access to the current season's data. When a user runs a scenario, it will use the feature functions to recalc features for the scenario, then use the model to predict, then render results. We need to ensure this is optimized (which it should be, as described). If using Streamlit, we might leverage caching (`@st.cache`) for the model loading and possibly for data fetch to speed things up.

### Reproducibility & Transparency

All code will be Python, which means we can easily share notebooks or scripts for how data was collected and how the model was built. We should maintain a `requirements.txt` of libraries (pandas, xgboost, streamlit, etc.) so that someone else can install and run the system. For transparency, we might also expose some of the model's internals in the app – e.g. allow a user to select two teams and compare their resumes side-by-side or even explain why the model ranked one higher (e.g. "Team A had 2 more top-25 wins and a tougher schedule, which our model heavily values"). This could be a valuable addition to gain user trust and interest, albeit not strictly required.

### Tech Stack Summary

- **Language**: Python (for everything).
- **Data access**: Requests/HTTP to CFBD API (or a local cache of that data), or possibly using the collegefootballdata Python library if available. Possibly use pandas for data manipulation.
- **ML**: XGBoost for training the ranking model; NumPy/Pandas for feature engineering.
- **Web UI**: Streamlit (a Python web app framework for data apps) to build the interface.
- **Visualization**: maybe Plotly or matplotlib if we want charts (e.g. we could chart the ranking scores or include graphs of each team's schedule difficulty vs rank).

This stack is quite common in sports analytics prototypes: you do the heavy-lifting in pandas and ML, then use Streamlit to make it interactive.

### Rapid Prototyping vs Traditional Web Development

Using Streamlit or Dash is a trade-off. Rapid prototyping tools are great for getting something working quickly and for iterative data-driven development. They might not handle thousands of concurrent users, but for our needs (likely a smaller user base of enthusiasts or as a portfolio project) it's fine. If this were to scale or become a public-facing site with many users, we might consider a more robust setup (a scalable backend, etc.). But the focus here is on the correctness and defensibility of the model, not on heavy web infrastructure.

### Example Implementation Flow

1. We create a training script that uses the data pipeline to assemble training data and train the XGBoost model. We save the model (say, `cfp_model.xgb`).
2. We create an app script (for Streamlit) that on startup loads `cfp_model.xgb` and also loads the latest data (or we embed the data if static for a given week).
3. The app shows a list of games (we can fetch upcoming games from the API or have the user pick a week and list games). The user selects outcomes and hits simulate.
4. The app then calls our simulation function with those selected outcomes, which returns a new rankings list and bracket info. We display those nicely (perhaps using tables for rankings and an image or text bracket for matchups).
5. We make sure to cite sources or link (maybe in an "About" page in the app, list that we used CFP data etc. – just to give credit and transparency).

By structuring in modules (`data.py`, `features.py`, `model.py`, `simulation.py`, `app.py` for example), each part can be developed and tested in isolation. For instance, we can unit test that flipping a game in `simulation.py` correctly changes a team's feature (e.g. if Team A was 10–1 and we flip a loss to a win, they become 11–0, SOS updates, etc.).

## Project Scope, MVP, and Pitfalls

It's important to define what constitutes a Minimum Viable Product (MVP) for this project versus more advanced enhancements, and to be aware of common pitfalls to avoid.

### MVP Features

A realistic MVP of the CFP predictor would include:

- A functioning data pipeline that can pull in at least one season's data (possibly hardcode some CSVs for quick start) and compute the necessary features.
- A trained model that can produce a reasonable approximation of committee rankings (it doesn't need to be perfect initially, but should at least get the top teams roughly right).
- A basic user interface (even if just a local Streamlit app) where the user can input a simple scenario (e.g. pick winners of a few key games) and see an output ranking and maybe which four teams would be in.
- For example, MVP might focus on predicting the final CFP rankings given all results (i.e. Selection Day outcome) rather than weekly updates. That simplifies data (only final records matter for a first version). It could answer "if these teams win their remaining games, who are the top 4?". This would already be a useful tool for playoff picture scenarios.
- Documented assumptions and a couple of example scenarios to demonstrate it works (e.g. show that if Georgia loses the SEC title game in the scenario, the model's playoff picks change accordingly).

### Advanced Version Features

Once the MVP is working, we can expand:

- Incorporate weekly ranking predictions (not just final week). That is, allow the user to pick a week in the season and simulate at that point. This requires handling partial season data and perhaps blending with AP poll for weeks before CFP rankings start (since first CFP ranking is mid-season, earlier weeks could use AP as a stand-in if needed).
- More granular user control, like editing scores (maybe not needed, since winner is what matters mostly).
- Visualization improvements: e.g. dynamic charts, perhaps a timeline of how rankings could change week over week under certain scenarios.
- More features or improved model: possibly include more nuanced stats (e.g. a metric for "game control" if we can derive it, or an improved SOS calculation). We could also try an ensemble of models or incorporate a neural net if we have more data by including AP poll data to pre-train, etc.
- Automated scenario generation: e.g. list the current playoff probabilities by simulating all reasonable combinations of wins/losses in remaining games (Monte Carlo simulation).
- User accounts or saving scenarios: if multiple people use it, maybe allow saving a scenario and sharing a link.

### Common Pitfalls in Sports Predictor Projects

**Overfitting to Past Data**: One big danger is that our model might overly fit quirks of the past 9 seasons which may not hold in future (especially with format change). We mitigate this by keeping the model relatively simple and focusing on core features. We also use validation on recent seasons to check that it still works on new data.

**Data Leakage**: We must ensure that when predicting a given week's ranking, we don't inadvertently use information from later games. For example, using a team's final record during mid-season would be leakage. Our pipeline is designed to avoid this by computing features week-by-week. We also must be careful when including any "season-long" metric like SOR – it should be computed up to the week of interest.

**Small sample size**: We only have as many training examples as team-weeks in committee ranking weeks (a few thousand). The model might not capture every edge case. For instance, the scenario of an undefeated Power 5 champ being left out (FSU 2023) never happened before 2023, so a model trained on earlier data would never predict leaving out an undefeated P5. Indeed our original model might have said FSU is definitely in. This is a case where the committee's decision was unprecedented (due to QB injury). We have to acknowledge such limitations – the model can only learn from what has happened. When new scenarios occur outside past patterns, the model could be wrong. We address this by adding in the criteria (we did have a feature for injuries? No, and it's hard to quantify). The best we can do is be transparent about such limitations.

**User Misinterpretation**: Users might assume the model is gospel. It's important to include disclaimers like "This is a projection based on historical committee behavior and does not guarantee actual rankings. It's for scenario exploration." We should highlight that the committee can be subjective and our model might not anticipate every human factor.

**Chasing media narratives**: Sometimes media or fans think the committee will do X but they do Y. Our model should stick to data, not narrative. For credibility, we rely on the committee's stated criteria and past actions, rather than, say, ESPN commentators' opinions (unless those align with what the committee does). We want a defensible stance: if someone asks "why did the model rank Team A over Team B?", we can point to concrete resume metrics rather than "the computer said so." Having the features makes this possible.

**Keeping data updated**: If we deploy this during a season, we need to update with each week's actual results before simulating new scenarios. We could automate fetching new results each week from CFBD. A pitfall is if data lags or a game isn't recorded, it could affect output. We should double-check data completeness (especially for something like conference championship designations, which might need manual input if the API doesn't provide it cleanly).

### Maintaining Credibility

To ensure the tool is taken seriously, we should:

- Clearly document the methodology (perhaps an "About" section or a blog write-up explaining the model).
- Cite sources and evidence for why features were chosen (e.g. "we include strength of schedule because the committee protocol says it's important").
- Show validation results: for example, "On the last three years of data, our model correctly predicted 10 of the 12 playoff teams and had a rank correlation of X with the committee." This gives users an idea of its accuracy and limitations.
- Not hide the limitations: e.g. "Our model does not account for injuries or off-field factors; if such a scenario arises (like a team losing its star quarterback late in season), the real committee might deviate from our model's expectation."
- Possibly allow users to see the "features" for each team (transparency). A small table like: Team, Record, SOS rank, Quality wins, Bad losses, etc., alongside the predicted ranking. This way users can understand the reasoning. It also invites feedback – if the model ranks something seemingly odd, the user can see maybe that team had a sneaky-tough schedule or something as per the data.

**Framing Limitations Honestly**: We might include a note like: "This model is based on historical data from the CFP committee decisions 2014–2023. It captures typical committee priorities (record, schedule strength, etc.) but cannot account for every subjective factor. The actual committee could always surprise us in unprecedented situations. Treat this as an informed projection, not a guarantee." Such honesty actually builds credibility, because it shows we understand the model's domain.

Additionally, we avoid copying any existing implementation code or proprietary logic. Everything is built from scratch with our own data pipeline and openly-known metrics. That keeps the project original. We might be inspired by others (like the Rankings Right Now project or analyst models) but we won't, for example, plug in their predictions – we produce our own via ML. This ensures the project is a valuable learning endeavor and a unique contribution.

## Conclusion and Next Steps

In this research, we've outlined how to design a CFP predictor web app from the ground up. We covered the CFP committee's selection process and rules – emphasizing the criteria like strength of schedule, head-to-head, conference championships, and how the new 12-team format is structured. We discussed the choice of modeling target, deciding on a continuous ranking score approach to best mimic the ordinal rankings. We identified data sources (especially the CollegeFootballData API) that make it feasible to gather all necessary historical data, and addressed alignment issues and changes over time. We proposed a rich set of features that encapsulate what the committee cares about, from win–loss record nuances to quality wins and beyond, justified by official statements and common practices. For the model, we chose XGBoost gradient boosting – a powerful yet interpretable method for this tabular ranking task – and outlined validation strategies to ensure the model reflects reality.

Crucially, we detailed the scenario simulation engine that ties it all together: how user-selected hypothetical results would ripple through team resumes and lead to a new ranking and playoff bracket, all computed quickly in Python code. Finally, we touched on the implementation stack (leaning toward Streamlit for the app) and considered project scope, acknowledging potential pitfalls (like subjective factors and data limitations) and emphasizing transparency and integrity in our approach.

The next steps would be to implement this plan: start coding the data pipeline, verify the data quality, train the model, and iteratively refine the features until the model's predictions align well with known committee decisions. Then build the UI and simulation around it. Testing with real-world scenarios (e.g., replay the 2022 season and see if the model's weekly rankings match the committee's) will be an important validation.

By grounding the project in historical committee behavior and clearly-defined metrics, we ensure that the predictor is not a black box but a explainable tool. It will allow fans (and researchers) to explore "if-then" questions like never before: What if my team wins out – do they control their destiny? What if there's chaos in championship week – who gets in? All based on data-driven analysis of how the committee has made such decisions in the past. With Python powering everything from data collection to machine learning to the web interface, the project will be fully reproducible and transparent, aligning with the user's emphasis on correctness and defensibility.

Ultimately, while our model can't read the minds of committee members, it can provide a reasoned projection of their decisions. This helps demystify the process and engages fans in understanding the nuances of the college football playoff race. The combination of a robust data pipeline, a well-chosen model, and an interactive UI will make for a compelling application that stands on solid research principles and provides real insight into the ever-passionate debate of "Who's in?" the College Football Playoff.

## Sources

- College Football Playoff Selection Committee official protocol and criteria
- News on CFP metric enhancements (strength of record)
- Historical analysis of predicting CFP selections
- CollegeFootballData.com API information (data source for games and rankings)
- User-provided project outline for feature and model design, confirming feasibility and approach


