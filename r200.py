import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

def get_ksvideosrc_device_indexes():
    device_index = 0
    video_src = Gst.ElementFactory.make('ksvideosrc')
    state_change_code = None

    while True:
        video_src.set_state(Gst.State.NULL)
        video_src.set_property('device-index', device_index)
        state_change_code = video_src.set_state(Gst.State.READY)
        if state_change_code != Gst.StateChangeReturn.SUCCESS:
            video_src.set_state(Gst.State.NULL)
            break
        device_index += 1
    return range(device_index)


if __name__ == '__main__':
    Gst.init(None)
    print(get_ksvideosrc_device_indexes())