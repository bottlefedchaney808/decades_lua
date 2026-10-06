package priest

import (
	"time"

	"github.com/wowsims/classic/sim/core"
)

func (priest *Priest) registerRenewSpell() {
	actionID := core.ActionID{SpellID: 25315}

	// Renew rank 7 = 25315 (level 60) — canonical id for this build.
	priest.Renew = make([]*core.Spell, 2)
	priest.Renew[1] = priest.GetOrRegisterSpell(core.SpellConfig{
		ActionID:    actionID,
		SpellSchool: core.SpellSchoolHoly,
		ProcMask:    core.ProcMaskSpellHealing,
		Flags:       SpellFlagPriest | core.SpellFlagHelpful | core.SpellFlagAPL,

		Rank:          1,
		RequiredLevel: 60,

		ManaCost: core.ManaCostOptions{BaseCost: 0.17},
		Cast: core.CastConfig{DefaultCast: core.Cast{GCD: core.GCDDefault}},

		DamageMultiplier: priest.renewHealingMultiplier(),
		ThreatMultiplier: 1 - []float64{0, .07, .14, .20}[priest.Talents.SilentResolve],

		Hot: core.DotConfig{
			Aura: core.Aura{Label: "Renew"},
			NumberOfTicks: priest.renewTicks(),
			TickLength:    time.Second * 3,
			OnSnapshot: func(sim *core.Simulation, target *core.Unit, dot *core.Dot, _ bool) {
				dot.SnapshotBaseDamage = 280
				dot.SnapshotAttackerMultiplier = 1
			},
			OnTick: func(sim *core.Simulation, target *core.Unit, dot *core.Dot) {
				dot.CalcAndDealPeriodicSnapshotHealing(sim, target, dot.OutcomeTick)
			},
		},

		ApplyEffects: func(sim *core.Simulation, target *core.Unit, spell *core.Spell) {
			spell.Hot(target).Apply(sim)
			if priest.EmpoweredRenew != nil {
				priest.EmpoweredRenew.Cast(sim, target)
			}
		},
	})
}

func (priest *Priest) renewTicks() int32 {
	return 5
}

func (priest *Priest) renewHealingMultiplier() float64 {
	return 1 *
		(1 + .02*float64(priest.Talents.SpiritualHealing)) *
		(1 + .05*float64(priest.Talents.ImprovedRenew))
}
