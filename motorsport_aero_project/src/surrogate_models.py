"""Optional holdout surrogate benchmark; never substitutes finalist simulation."""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,root_mean_squared_error
from .config import CONFIG

def fit_holdout(evaluations):
    """One row per unique setup: split setups, not correlated telemetry rows."""
    df=evaluations.loc[evaluations.feasible].drop_duplicates(list(CONFIG["bounds"]))
    x=df[list(CONFIG["bounds"])]; y=df.lap_time_s
    a,b,c,d=train_test_split(x,y,test_size=.25,random_state=42)
    model=RandomForestRegressor(n_estimators=100,min_samples_leaf=2,random_state=42).fit(a,c)
    pred=model.predict(b)
    return model,{"holdout_setups":len(b),"mae_s":mean_absolute_error(d,pred),"rmse_s":root_mean_squared_error(d,pred),"reference_type":"direct synthetic simulator"}
