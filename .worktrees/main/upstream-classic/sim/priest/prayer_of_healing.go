package priest

import (
	"time"

	"github.com/wowsims/classic/sim/core"
)

func (priest *Priest) registerPrayerOfHealingSpell() {
	// Prayer of Healing rank 5 = 10961 (level 60) — canonical id for this build.
	priest.PrayerOfHealing = make([]*core.Spell, 2)
	priest.PrayerOfHealing[1] = priest.GetOrRegisterSpell(core.SpellConfig{
		ActionID:    core.ActionID{SpellID: 10961},
		SpellSchool: core.SpellSchoolHoly,
		DefenseType: core.DefenseTypeMagic,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       SpellFlagPriest | core.SpellFlagHelpful | core.SpellFlagAPL,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.48},
		Cast: core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault, CastTime: time.Second * 3}},

		BonusCritRating:  float64(priest.Talents.HolySpecialization),
		DamageMultiplier: 1 + .02*float64(priest.Talents.SpiritualHealing),
		ThreatMultiplier: 1 - []float64{0, .07, .14, .20}[priest.Talents.SilentResolve],

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			targetAgent := target.Env.Raid.GetPlayerFromUnitIndex(target.UnitIndex)
			party := targetAgent.GetCharacter().Party
			for _, partyAgent := range party.PlayersAndPets {
				partyTarget := &partyAgent.GetCharacter().Unit
				baseHealing := sim.Roll(2109, 2228) + 0.526*spell.HealingPower(partyTarget)
				spell.CalcAndDealHealing(sim, partyTarget, baseHealing, spell.OutcomeHealingCrit)
			}
		},
	})
}
