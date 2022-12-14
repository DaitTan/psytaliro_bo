# import numpy as np
# from staliro.models import blackbox, SignalTimes, SignalValues
# from staliro.core.model import Model, ModelData

# try:
#     import matlab
#     import matlab.engine
# except ImportError:
#     _has_matlab = False
# else:
#     _has_matlab = True


# eng = matlab.engine.start_matlab()
# MODEL_NAME = "Autotrans_shift"
# mo = eng.simget(MODEL_NAME)
# model_opts = eng.simset(mo, "SaveFormat", "Array")


# def _dosim(T:SignalTimes, U:SignalValues):
#     sim_t = matlab.double([0, max(T)])
#     # n_times = (max(T) // 0.01) + 1
#     # signal_times = np.linspace(min(T), max(T), int(n_times))
#     # print(f"Signal_times = {signal_times.shape}")
#     # signal_values = np.array(
#     #     [[signal.at_time(t) for t in signal_times] for signal in U]
#     # )
#     # print(f"Signal_values = {signal_values.shape}")
#     print(T.shape)
#     print(U.shape)
#     print(T)
#     print(U)
#     model_input = matlab.double(np.row_stack((T, U)).T.tolist())


#     timestamps, _, data = eng.sim(
#         MODEL_NAME, sim_t, model_opts, model_input, nargout=3
#     )

#     timestamps_array = np.array(timestamps).flatten()
#     data_array = np.array(data)

#     return data_array.T, timestamps_array


# @blackbox
# def autotrans_blackbox(_, T:SignalTimes, U:SignalValues):
#     trajectories, timestamps = _dosim(T, U)
    
#     return ModelData(trajectories, timestamps)

import numpy as np
from numpy.typing import NDArray
from staliro.core.interval import Interval
from staliro.core.model import Model, ModelData, Failure, StaticInput, Signals
from staliro.options import Options, SignalOptions
from staliro.specifications import RTAMTDense
from staliro.staliro import staliro, simulate_model

#############################################################

try:
    import matlab
    import matlab.engine
except ImportError:
    _has_matlab = False
else:
    _has_matlab = True

AutotransDataT = NDArray[np.float_]
AutotransResultT = ModelData[AutotransDataT, None]


class AutotransModel(Model[AutotransDataT, None]):
    MODEL_NAME = "Autotrans_shift"

    def __init__(self) -> None:
        if not _has_matlab:
            raise RuntimeError(
                "Simulink support requires the MATLAB Engine for Python to be installed"
            )

        engine = matlab.engine.start_matlab()
        # engine.addpath("examples")
        model_opts = engine.simget(self.MODEL_NAME)

        self.sampling_step = 0.05
        self.engine = engine
        self.model_opts = engine.simset(model_opts, "SaveFormat", "Array")

    def simulate(self, static: StaticInput, signals: Signals, intrvl: Interval) -> AutotransResultT:
        sim_t = matlab.double([0, intrvl.upper])
        n_times = (intrvl.length // self.sampling_step) + 2
        signal_times = np.linspace(intrvl.lower, intrvl.upper, int(n_times))
        signal_values = np.array([[signal.at_time(t) for t in signal_times] for signal in signals])

        model_input = matlab.double(np.row_stack((signal_times, signal_values)).T.tolist())
        
        timestamps, _, data = self.engine.sim(
            self.MODEL_NAME, sim_t, self.model_opts, model_input, nargout=3
        )

        timestamps_array = np.array(timestamps).flatten()
        data_array = np.array(data)

        return ModelData(data_array.T, timestamps_array)
