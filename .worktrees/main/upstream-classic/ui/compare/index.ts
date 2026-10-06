import { Sim } from '../core/sim.js';
import { Player } from '../core/player.js';
import { TypedEvent } from '../core/typed_event.js';
import { Spec } from '../core/proto/common.js';
import { SimResult } from '../core/proto_utils/sim_result.js';
import { DistributionMetrics } from '../core/proto/api.js';

// Import every spec's sim module so its config is registered in SPEC_CONFIGS
// and its UI class is available. These are all pure forwarders of the base
// IndividualSimUI, so each panel is a fully functional individual sim.
import { BalanceDruidSimUI } from '../balance_druid/sim.js';
import { ElementalShamanSimUI } from '../elemental_shaman/sim.js';
import { EnhancementShamanSimUI } from '../enhancement_shaman/sim.js';
import { FeralDruidSimUI } from '../feral_druid/sim.js';
import { FeralTankDruidSimUI } from '../feral_tank_druid/sim.js';
import { HealingPriestSimUI } from '../healing_priest/sim.js';
import { HolyPaladinSimUI } from '../holy_paladin/sim.js';
import { HunterSimUI } from '../hunter/sim.js';
import { MageSimUI } from '../mage/sim.js';
import { ProtectionPaladinSimUI } from '../protection_paladin/sim.js';
import { RestorationDruidSimUI } from '../restoration_druid/sim.js';
import { RestorationShamanSimUI } from '../restoration_shaman/sim.js';
import { RetributionPaladinSimUI } from '../retribution_paladin/sim.js';
import { RogueSimUI } from '../rogue/sim.js';
import { ShadowPriestSimUI } from '../shadow_priest/sim.js';
import { TankWarriorSimUI } from '../tank_warrior/sim.js';
import { WardenShamanSimUI } from '../warden_shaman/sim.js';
import { WarlockSimUI } from '../warlock/sim.js';
import { WarriorSimUI } from '../warrior/sim.js';

const SPEC_UI: Record<Spec, { name: string; make: (parent: HTMLElement, player: Player<any>) => any }> = {
	[Spec.SpecBalanceDruid]: { name: 'Balance Druid', make: (p, pl) => new BalanceDruidSimUI(p, pl as Player<Spec.SpecBalanceDruid>) },
	[Spec.SpecElementalShaman]: { name: 'Elemental Shaman', make: (p, pl) => new ElementalShamanSimUI(p, pl as Player<Spec.SpecElementalShaman>) },
	[Spec.SpecEnhancementShaman]: { name: 'Enhancement Shaman', make: (p, pl) => new EnhancementShamanSimUI(p, pl as Player<Spec.SpecEnhancementShaman>) },
	[Spec.SpecFeralDruid]: { name: 'Feral Druid', make: (p, pl) => new FeralDruidSimUI(p, pl as Player<Spec.SpecFeralDruid>) },
	[Spec.SpecFeralTankDruid]: { name: 'Feral Tank Druid', make: (p, pl) => new FeralTankDruidSimUI(p, pl as Player<Spec.SpecFeralTankDruid>) },
	[Spec.SpecHealingPriest]: { name: 'Healing Priest', make: (p, pl) => new HealingPriestSimUI(p, pl as Player<Spec.SpecHealingPriest>) },
	[Spec.SpecHolyPaladin]: { name: 'Holy Paladin', make: (p, pl) => new HolyPaladinSimUI(p, pl as Player<Spec.SpecHolyPaladin>) },
	[Spec.SpecHunter]: { name: 'Hunter', make: (p, pl) => new HunterSimUI(p, pl as Player<Spec.SpecHunter>) },
	[Spec.SpecMage]: { name: 'Mage', make: (p, pl) => new MageSimUI(p, pl as Player<Spec.SpecMage>) },
	[Spec.SpecProtectionPaladin]: { name: 'Protection Paladin', make: (p, pl) => new ProtectionPaladinSimUI(p, pl as Player<Spec.SpecProtectionPaladin>) },
	[Spec.SpecRestorationDruid]: { name: 'Restoration Druid', make: (p, pl) => new RestorationDruidSimUI(p, pl as Player<Spec.SpecRestorationDruid>) },
	[Spec.SpecRestorationShaman]: { name: 'Restoration Shaman', make: (p, pl) => new RestorationShamanSimUI(p, pl as Player<Spec.SpecRestorationShaman>) },
	[Spec.SpecRetributionPaladin]: { name: 'Retribution Paladin', make: (p, pl) => new RetributionPaladinSimUI(p, pl as Player<Spec.SpecRetributionPaladin>) },
	[Spec.SpecRogue]: { name: 'Rogue', make: (p, pl) => new RogueSimUI(p, pl as Player<Spec.SpecRogue>) },
	[Spec.SpecShadowPriest]: { name: 'Shadow Priest', make: (p, pl) => new ShadowPriestSimUI(p, pl as Player<Spec.SpecShadowPriest>) },
	[Spec.SpecTankWarrior]: { name: 'Tank Warrior', make: (p, pl) => new TankWarriorSimUI(p, pl as Player<Spec.SpecTankWarrior>) },
	[Spec.SpecWardenShaman]: { name: 'Warden Shaman', make: (p, pl) => new WardenShamanSimUI(p, pl as Player<Spec.SpecWardenShaman>) },
	[Spec.SpecWarlock]: { name: 'Warlock', make: (p, pl) => new WarlockSimUI(p, pl as Player<Spec.SpecWarlock>) },
	[Spec.SpecWarrior]: { name: 'Warrior', make: (p, pl) => new WarriorSimUI(p, pl as Player<Spec.SpecWarrior>) },
};

interface Panel {
	spec: Spec;
	sim: Sim;
	player: Player<any>;
	ui: any;
	result: SimResult | null;
}

function makeSpecSelect(el: HTMLSelectElement, value: Spec) {
	el.innerHTML = '';
	for (const spec of Object.keys(SPEC_UI).map(k => Number(k) as Spec)) {
		const opt = document.createElement('option');
		opt.value = String(spec);
		opt.textContent = SPEC_UI[spec].name;
		el.appendChild(opt);
	}
	el.value = String(value);
}

function buildPanel(side: 'left' | 'right', spec: Spec): Panel {
	const host = document.getElementById(`panel-${side}`)!;
	host.innerHTML = '';
	document.getElementById(`panel-${side}-title`)!.textContent = SPEC_UI[spec].name;

	const sim = new Sim();
	const player = new Player<any>(spec, sim);
	sim.raid.setPlayer(TypedEvent.nextEventID(), 0, player);
	const ui = SPEC_UI[spec].make(host, player);

	const panel: Panel = { spec, sim, player, ui, result: null };
	sim.simResultEmitter.on((_eventID, simResult) => {
		if (simResult instanceof SimResult) {
			panel.result = simResult;
			renderCompare();
		}
	});
	return panel;
}

function fmt(v: number): string {
	return v.toFixed(2);
}

function distAvg(d?: DistributionMetrics): number | null {
	return d && d.avg > 0 ? d.avg : null;
}

// Row: label, left value, right value. The better (higher) side is highlighted.
function row(label: string, left: number | null, right: number | null): string {
	if (left == null && right == null) return '';
	const l = left == null ? '—' : fmt(left);
	const r = right == null ? '—' : fmt(right);
	let lCls = '', rCls = '';
	if (left != null && right != null) {
		if (left > right) lCls = 'better';
		else if (right > left) rCls = 'better';
	}
	return `<tr><td>${label}</td><td class="num ${lCls}">${l}</td><td class="num ${rCls}">${r}</td></tr>`;
}

function playerDist(result: SimResult | null, key: 'dps' | 'hps' | 'threat'): number | null {
	if (!result) return null;
	const p = result.raidMetrics.parties[0]?.players[0] as unknown as { dps?: DistributionMetrics; hps?: DistributionMetrics; threat?: DistributionMetrics };
	return distAvg(p?.[key]);
}
function raidDist(result: SimResult | null, key: 'dps' | 'hps'): number | null {
	if (!result) return null;
	return distAvg(result.raidMetrics[key]);
}

function renderCompare() {
	const left = panels.left;
	const right = panels.right;
	const table = document.getElementById('compare-table')!;
	const status = document.getElementById('compare-status')!;

	const rows: Array<[string, number | null, number | null]> = [
		['Raid DPS (avg)', raidDist(left.result, 'dps'), raidDist(right.result, 'dps')],
		['Raid HPS (avg)', raidDist(left.result, 'hps'), raidDist(right.result, 'hps')],
		['Player DPS', playerDist(left.result, 'dps'), playerDist(right.result, 'dps')],
		['Player HPS', playerDist(left.result, 'hps'), playerDist(right.result, 'hps')],
		['Player Threat', playerDist(left.result, 'threat'), playerDist(right.result, 'threat')],
	];

	let html = '<thead><tr><th>Metric</th><th class="num">Left</th><th class="num">Right</th></tr></thead><tbody>';
	for (const [label, l, r] of rows) {
		html += row(label, l, r);
	}
	html += '</tbody>';
	table.innerHTML = html;

	const done = [left.result, right.result].filter(Boolean).length;
	const total = 2;
	status.textContent = done === total
		? `Compared ${SPEC_UI[left.spec].name} vs ${SPEC_UI[right.spec].name}.`
		: `Waiting for results (${done}/${total} complete)...`;
}

const panels: { left: Panel; right: Panel } = { left: null as any, right: null as any };

const selLeft = document.getElementById('spec-left') as HTMLSelectElement;
const selRight = document.getElementById('spec-right') as HTMLSelectElement;
const runBtn = document.getElementById('run-both') as HTMLButtonElement;

function rebuild(side: 'left' | 'right', spec: Spec) {
	panels[side] = buildPanel(side, spec);
}

selLeft.addEventListener('change', () => {
	rebuild('left', Number(selLeft.value) as Spec);
	document.getElementById('compare-results')!.style.display = 'none';
});
selRight.addEventListener('change', () => {
	rebuild('right', Number(selRight.value) as Spec);
	document.getElementById('compare-results')!.style.display = 'none';
});

runBtn.addEventListener('click', async () => {
	runBtn.disabled = true;
	document.getElementById('compare-results')!.style.display = 'block';
	renderCompare();
	try {
		await Promise.all([
			panels.left.ui.runSim((_p: any) => {}),
			panels.right.ui.runSim((_p: any) => {}),
		]);
	} catch (e) {
		console.error('Compare run error', e);
	}
	runBtn.disabled = false;
});

// Initial panels.
makeSpecSelect(selLeft, Spec.SpecMage);
makeSpecSelect(selRight, Spec.SpecRogue);
rebuild('left', Spec.SpecMage);
rebuild('right', Spec.SpecRogue);
