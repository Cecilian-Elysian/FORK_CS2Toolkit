use serde::Deserialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Event {
    None,
    Died,
    Returned,
}

#[derive(Debug, Default)]
pub struct DeathDetector {
    initialized: bool,
    was_dead: bool,
    was_spectating: bool,
    last_phase: String,
}

#[derive(Debug, Deserialize)]
pub struct GameState {
    #[serde(default)]
    pub provider: Provider,
    #[serde(default)]
    pub player: Player,
    #[serde(default)]
    pub round: Round,
}

#[derive(Debug, Default, Deserialize)]
pub struct Provider {
    #[serde(default)]
    pub steamid: String,
}

#[derive(Debug, Default, Deserialize)]
pub struct Player {
    #[serde(default)]
    pub steamid: String,
    #[serde(default)]
    pub team: String,
    #[serde(default)]
    pub activity: String,
    pub spectarget: Option<String>,
    #[serde(default)]
    pub state: PlayerState,
}

#[derive(Debug, Default, Deserialize)]
pub struct PlayerState {
    pub health: Option<i32>,
}

#[derive(Debug, Default, Deserialize)]
pub struct Round {
    #[serde(default)]
    pub phase: String,
}

impl DeathDetector {
    pub fn process(&mut self, state: &GameState) -> Event {
        let spectating = is_spectating(state);
        let health = state.player.state.health;
        let is_dead = matches!(health, Some(0));
        let entered_freezetime =
            state.round.phase == "freezetime" && self.last_phase != "freezetime";

        if !self.initialized {
            self.initialized = true;
            self.was_dead = is_dead;
            self.was_spectating = spectating;
            self.last_phase.clone_from(&state.round.phase);
            return Event::None;
        }

        let event = if self.was_dead
            && ((matches!(health, Some(value) if value > 0) && !spectating) || entered_freezetime)
        {
            Event::Returned
        } else if !self.was_dead && is_dead && !spectating && !self.was_spectating {
            Event::Died
        } else {
            Event::None
        };

        self.was_dead = is_dead;
        self.was_spectating = spectating;
        self.last_phase.clone_from(&state.round.phase);
        event
    }
}

fn is_spectating(state: &GameState) -> bool {
    let player = &state.player;
    (!state.provider.steamid.is_empty()
        && !player.steamid.is_empty()
        && state.provider.steamid != player.steamid)
        || player.spectarget.is_some()
        || player.activity == "spectating"
        || !matches!(player.team.as_str(), "T" | "CT")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn state(health: i32, phase: &str) -> GameState {
        serde_json::from_str(&format!(
            r#"{{"provider":{{"steamid":"1"}},"player":{{"steamid":"1","team":"CT","state":{{"health":{health}}}}},"round":{{"phase":"{phase}"}}}}"#
        ))
        .unwrap()
    }

    #[test]
    fn detects_a_single_death_and_return() {
        let mut detector = DeathDetector::default();
        assert_eq!(detector.process(&state(100, "live")), Event::None);
        assert_eq!(detector.process(&state(0, "live")), Event::Died);
        assert_eq!(detector.process(&state(0, "live")), Event::None);
        assert_eq!(detector.process(&state(100, "live")), Event::Returned);
    }

    #[test]
    fn initial_dead_packet_does_not_switch() {
        let mut detector = DeathDetector::default();
        assert_eq!(detector.process(&state(0, "live")), Event::None);
    }

    #[test]
    fn returns_on_new_round() {
        let mut detector = DeathDetector::default();
        detector.process(&state(100, "live"));
        assert_eq!(detector.process(&state(0, "live")), Event::Died);
        assert_eq!(detector.process(&state(0, "freezetime")), Event::Returned);
    }
}
