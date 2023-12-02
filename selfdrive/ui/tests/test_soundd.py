import numpy as np
import pytest
import unittest
import time

from cereal import messaging, car
from openpilot.selfdrive.test.helpers import with_processes


AudibleAlert = car.CarControl.HUDControl.AudibleAlert


@pytest.mark.tici
class TestSoundd(unittest.TestCase):
  SOUND_PLAY_TIME = 1
  TOL = 0.2

  def _test_sound_level(self, db, ambient_db):
    self.assertGreater(db, ambient_db + 5)

  @with_processes(["soundd", "micd"])
  def test_sound(self):
    time.sleep(2)

    pm = messaging.PubMaster(['controlsState'])
    sm = messaging.SubMaster(['microphone'])

    sounds_to_play = [AudibleAlert.engage, AudibleAlert.disengage, AudibleAlert.refuse, AudibleAlert.prompt, \
                    AudibleAlert.promptRepeat, AudibleAlert.promptDistracted, AudibleAlert.warningSoft, AudibleAlert.warningImmediate]

    for i in range(len(sounds_to_play)):
      def send_sound(sound, play_time):
        db_history = []

        play_start = time.monotonic()
        while time.monotonic() - play_start < play_time:
          sm.update(0)

          if sm.updated['microphone']:
            db_history.append(sm["microphone"].soundPressureWeightedDb)

          m1 = messaging.new_message('controlsState')
          m1.controlsState.alertSound = sound

          pm.send('controlsState', m1)
          time.sleep(0.01)

        if sound == AudibleAlert.none:
          self.ambient_db = np.mean(db_history)
        else:
          self._test_sound_level(np.mean(db_history), self.ambient_db)

      send_sound(AudibleAlert.none, self.SOUND_PLAY_TIME*2)
      send_sound(sounds_to_play[i], self.SOUND_PLAY_TIME)


if __name__ == "__main__":
  unittest.main()