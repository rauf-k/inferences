# inferences
Inference data for Amazon on 2021-12-28

Columns contain following info:
Column A: moving average of price tick data. Moving average interval = 3.
Column B: raw output from the model for buy probability.
Column C: binarization of buy probability by applying a threshold of 0.12565 to raw output.

Notes:
- sell probability is not yet available as im currently tuning the model.
- model was trained on Amazon tick data ranging from 2020-12-15 to 2021-02-19. Not all data from this range was used, it was randomly subsampled.
- inference was performed on Amazon tick data for 2021-12-28.
