import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

// Data layer decoupled from UI. 
// Maintains the roster in Pokédex order while isolating descriptions from the render logic.
const ROSTER_DATA = [
  {
    region: "Kanto",
    entities: [
      { name: "Articuno", category: "Legendary", description: "Channels freezing energy before unleashing a flurry of icy pillars that rain down from the top of the monitor. Any pets struck by the falling ice are instantly frozen solid in a block of ice." },
      { name: "Zapdos", category: "Legendary", description: "Explodes with electric energy, summoning violent lightning bolts that strike down randomly across the screen. The high-voltage strikes instantly paralyze any pets unfortunate enough to be hit by the pillars." },
      { name: "Moltres", category: "Legendary", description: "Bursts with fiery energy, causing scorching pillars of flame to erupt violently from the bottom of the screen. Pets caught in the blazing updrafts are blasted by the heat and severely burned." },
      { name: "Mewtwo", category: "Legendary", description: "Levitates with a psychic aura and forcefully pulls other pets into a massive, rapidly accelerating orbital ring around itself. After spinning them through the air, it unleashes a purple energy burst that hurls the trapped pets away at high speeds." },
      { name: "Mew", category: "Mythical", description: "Bounces rapidly around the screen boundaries inside a glowing pink bubble, leaving a sparkling trail. It captures nearby pets in smaller bubbles, tethering them with a genetic double-helix link and pulling them into its orbit before popping to drop them." }
    ]
  },
  {
    region: "Johto",
    entities: [
      { name: "Raikou", category: "Legendary", description: "Emits a powerful roar that summons crackling fractal lightning bolts branching outwards. The high-voltage shockwave instantly paralyzes any nearby pets, stopping them in their tracks." },
      { name: "Entei", category: "Legendary", description: "Unleashes a thunderous roar that triggers a massive, erupting burst of fiery particles. The intense heat of the explosion severely burns any pets caught within its wide radius." },
      { name: "Suicune", category: "Legendary", description: "Roars to summon massive, aerodynamic water waves that surge horizontally and crash against the screen edges. Any pets caught in the sweeping tide are swept up and forcefully thrown away by the hydrodynamic current." },
      { name: "Lugia", category: "Legendary", description: "Dives off-screen before performing a massive, high-speed horizontal dash across your monitor, violently shaking the PC window. The sheer aerodynamic force creates a visual wind tunnel that blows all other pets away at high speeds." },
      { name: "Ho-Oh", category: "Legendary", description: "Flies to the top of the screen and unleashes a massive 360-degree nova of fire particles, inflicting pure terror upon all other pets. The terrified pets are forced into a frantic panic, running back and forth across your desktop with flames trailing at their feet." },
      { name: "Celebi", category: "Mythical", description: "Channels a spiraling energy blast that freezes time, suspending all other pets in mid-air as translucent, immobile ghosts. It then flies directly to each frozen pet, striking them with a burst of pink light to restore them to normal gravity and behavior." }
    ]
  },
  {
    region: "Hoenn",
    entities: [
      { name: "Regirock", category: "Legendary", description: "Approaches a target and violently launches them through the air with a brutal physical strike. The sheer force of the impact causes the victim to become physically embedded into the screen's walls or floor upon crashing." },
      { name: "Regice", category: "Legendary", description: "Approaches a nearby target and delivers a powerful strike that sends them flying into the air. When the victim finally crashes into the floor, they are instantly encased and frozen in a block of ice." },
      { name: "Registeel", category: "Legendary", description: "Steadily approaches a nearby pet and delivers a devastating metallic strike that generates a shockwave. The intense impact sends the victim hurtling across the screen with massive force." },
      { name: "Latias", category: "Legendary" },
      { name: "Latios", category: "Legendary" },
      { name: "Kyogre", category: "Legendary", description: "Channels aquatic energy to summon a massive deluge of water that floods the bottom of your screen. Other pets are caught in the rising tide, floating helplessly and drifting along the water's wavy surface." },
      { name: "Groudon", category: "Legendary", description: "Leaps into the air and crashes down with immense force, triggering a violent earthquake that physically shakes the user's active window. The massive shockwave forcefully launches all grounded pets into the air, instantly canceling whatever they were doing and scattering them with dirt." },
      { name: "Rayquaza", category: "Legendary", description: "Flies to the top of the screen and performs rapid horizontal sweeps while conjuring intense emerald cyclones. The swirling vortex aggressively sucks up all other pets, dragging them back and forth across the sky before hurling them away." },
      { name: "Jirachi", category: "Mythical", description: "Channels energy inside a glowing golden star before teleporting away and flying horizontally across your entire screen, leaving a glittering trail in its wake. As it passes, it summons a shower of falling stars that bounce off windows and grant a glowing speed buff to any pet they strike." },
      { name: "Deoxys", category: "Mythical" }
    ]
  },
  {
    region: "Sinnoh",
    entities: [
      { name: "Uxie", category: "Legendary" },
      { name: "Mesprit", category: "Legendary" },
      { name: "Azelf", category: "Legendary" },
      { name: "Dialga", category: "Legendary", description: "Slams violently into the bottom of a window to unleash a temporal shockwave, enveloping itself and all other pets in pulsating ripples of purple and blue energy. This time distortion effect visually alters the pets with continuous energy pulses as they move around the screen." },
      { name: "Palkia", category: "Legendary", description: "Slams into the bottom of the screen to trigger a spatial distortion aura filled with glowing pink rifts. This reality-bending effect temporarily inverts gravity for all other pets, forcing them to fall upward and walk on the ceiling." },
      { name: "Heatran", category: "Legendary" },
      { name: "Regigigas", category: "Legendary", description: "Slowly marches toward a target pet, grabs it, and violently throws it while shaking your actual PC window. The thrown pet bounces around, creating shockwaves and a final global earthquake that embeds it into the screen." },
      { name: "Giratina", category: "Legendary", description: "Tears open a dark, swirling vortex on your screen with glowing red eyes that forcefully pulls in and completely absorbs all other pets. It then dashes across the screen and reappears later to violently eject the trapped pets back onto your desktop through miniature portals." },
      { name: "Cresselia", category: "Legendary", description: "Ascends to the top of the screen and summons a glowing aurora that showers colorful light downward. This light blesses all other pets, making them pulse brightly and sprint rapidly back and forth across the desktop." },
      { name: "Phione", category: "Mythical" },
      { name: "Manaphy", category: "Mythical" },
      { name: "Darkrai", category: "Mythical", description: "Teleports to the center of the screen to channel a massive dark field that magnetically pulls in all other pets. Once caught in the shadow, pets are trapped in a nightmare where they uncontrollably spin and bounce rapidly off the screen edges." },
      { name: "Shaymin", category: "Mythical" },
      { name: "Arceus", category: "Mythical" }
    ]
  },
  {
    region: "Unova",
    entities: [
      { name: "Victini", category: "Mythical" },
      { name: "Cobalion", category: "Legendary" },
      { name: "Terrakion", category: "Legendary" },
      { name: "Virizion", category: "Legendary" },
      { name: "Tornadus", category: "Legendary" },
      { name: "Thundurus", category: "Legendary" },
      { name: "Reshiram", category: "Legendary", description: "Conjures a massive sphere of fire and hurls it at the bottom of the screen, triggering a huge fiery shockwave upon impact. Any pet caught in the blast area is set on fire, causing them to panic and run frantically around the screen." },
      { name: "Zekrom", category: "Legendary", description: "Envelops itself in a pulsing electric aura and flies upward before dive-bombing back to the ground. The impact releases a massive cyan shockwave across the screen that paralyzes all other pets, trapping them in a stunned state." },
      { name: "Landorus", category: "Legendary" },
      { name: "Kyurem", category: "Legendary", description: "Unleashes a wide-reaching blast of icy wind that scatters freezing particles across the screen. Any pets caught in the chilling area are frozen into solid ice cubes, causing them to slide uncontrollably and bounce off the screen's edges." },
      { name: "Keldeo", category: "Mythical" },
      { name: "Meloetta", category: "Mythical" },
      { name: "Genesect", category: "Mythical" }
    ]
  },
  {
    region: "Kalos",
    entities: [
      { name: "Xerneas", category: "Legendary", description: "Projects a wide, shimmering pink fairy aura around itself. Any pets that wander into this radius are immediately pacified, stopping their chaotic actions to peacefully walk around Xerneas." },
      { name: "Yveltal", category: "Legendary", description: "Fires a devastating dark red beam downward that erupts into a massive dark explosion upon hitting the ground. Any pet caught in the beam's path or the resulting blast is temporarily turned into solid stone and unable to move." },
      { name: "Zygarde", category: "Legendary", description: "Depending on its form, it either dashes across the screen or sits centrally while emitting green hexagonal cells. It acts as a global artillery unit, firing green arrows to shoot flying pets out of the air, or summoning earth pillars to launch grounded pets upward." },
      { name: "Diancie", category: "Mythical" },
      { name: "Hoopa", category: "Mythical" },
      { name: "Volcanion", category: "Mythical" }
    ]
  },
  {
    region: "Alola",
    entities: [
      { name: "Type: Null", category: "Legendary" },
      { name: "Silvally", category: "Legendary" },
      { name: "Tapu Koko", category: "Legendary" },
      { name: "Tapu Lele", category: "Legendary" },
      { name: "Tapu Bulu", category: "Legendary" },
      { name: "Tapu Fini", category: "Legendary" },
      { name: "Cosmog", category: "Legendary" },
      { name: "Cosmoem", category: "Legendary" },
      { name: "Solgaleo", category: "Legendary", description: "Transforms into a blazing fireball and crashes down onto the screen, unleashing a massive kinetic explosion. This shockwave forcefully knocks all nearby pets away, interrupting any of their current actions." },
      { name: "Lunala", category: "Legendary", description: "Channels a massive purple and blue energy beam towards the bottom of the screen that detonates into a giant shockwave. The blast violently knocks back any other pets caught in its radius, cancelling their current actions and sending them flying." },
      { name: "Nihilego", category: "Ultra Beast" },
      { name: "Buzzwole", category: "Ultra Beast" },
      { name: "Pheromosa", category: "Ultra Beast" },
      { name: "Xurkitree", category: "Ultra Beast" },
      { name: "Celesteela", category: "Ultra Beast" },
      { name: "Kartana", category: "Ultra Beast" },
      { name: "Guzzlord", category: "Ultra Beast" },
      { name: "Necrozma", category: "Legendary", description: "Devours light into its core before firing a barrage of glowing projectiles that ricochet off the screen's edges. Pets struck by these projectiles are cursed with a creeping darkness effect, while the stolen light makes Necrozma temporarily grow larger and brighter." },
      { name: "Magearna", category: "Mythical" },
      { name: "Marshadow", category: "Mythical" },
      { name: "Poipole", category: "Ultra Beast" },
      { name: "Naganadel", category: "Ultra Beast" },
      { name: "Stakataka", category: "Ultra Beast" },
      { name: "Blacephalon", category: "Ultra Beast" },
      { name: "Zeraora", category: "Mythical" },
      { name: "Meltan", category: "Mythical" },
      { name: "Melmetal", category: "Mythical" }
    ]
  },
  {
    region: "Galar & Hisui",
    entities: [
      { name: "Zacian", category: "Legendary", description: "Absorbs energy before executing a lightning-fast horizontal dash across the screen, leaving a glowing slash trail. Any pets caught in its path are violently stunned and sent flying backward." },
      { name: "Zamazenta", category: "Legendary", description: "Summons a massive energy shield in front of itself and charges rapidly across the screen, scooping up any pets in its way. Upon hitting the screen's edge, it releases an explosion that launches all the collected pets high into the air." },
      { name: "Eternatus", category: "Legendary", description: "Ascends off-screen and fires a massive, screen-piercing pink Eternabeam that forcefully injects dynamax energy into any grounded pet caught in its path. Affected pets absorb the blast and grow to an enormous size with red storm clouds orbiting them, before explosively shrinking back down." },
      { name: "Kubfu", category: "Legendary" },
      { name: "Urshifu", category: "Legendary" },
      { name: "Zarude", category: "Mythical" },
      { name: "Regieleki", category: "Legendary", description: "Zips across the screen at lightning speed to strike a targeted pet, violently launching them into the air. Upon crashing back down, the victim is left severely paralyzed by the lingering electric shock." },
      { name: "Regidrago", category: "Legendary", description: "Approaches a target and unleashes a draconic strike that blasts the pet away with a localized shockwave. The lingering draconic energy causes the victim's movements to become significantly slowed once they land." },
      { name: "Glastrier", category: "Legendary" },
      { name: "Spectrier", category: "Legendary" },
      { name: "Calyrex", category: "Legendary" },
      { name: "Enamorus", category: "Legendary" }
    ]
  },
  {
    region: "Paldea & Kitakami",
    entities: [
      { name: "Wo-Chien", category: "Legendary" },
      { name: "Chien-Pao", category: "Legendary" },
      { name: "Ting-Lu", category: "Legendary" },
      { name: "Chi-Yu", category: "Legendary" },
      { name: "Koraidon", category: "Legendary", description: "Climbs the screen's edge and leaps into the air before diving aggressively at a targeted pet. The resulting impact creates a massive fiery shockwave that violently knocks all other pets away from the blast zone." },
      { name: "Miraidon", category: "Legendary", description: "Dashes aggressively across the screen boundaries, leaving a bright electric trail that paralyzes any pets it touches with a robotic jitter. The frantic dash culminates in an electric shockwave that violently knocks back all pets in its radius." },
      { name: "Walking Wake", category: "Legendary" },
      { name: "Iron Leaves", category: "Legendary" },
      { name: "Okidogi", category: "Legendary" },
      { name: "Munkidori", category: "Legendary" },
      { name: "Fezandipiti", category: "Legendary" },
      { name: "Ogerpon", category: "Legendary" },
      { name: "Gouging Fire", category: "Legendary" },
      { name: "Raging Bolt", category: "Legendary" },
      { name: "Iron Boulder", category: "Legendary" },
      { name: "Iron Crown", category: "Legendary" },
      { name: "Terapagos", category: "Legendary" },
      { name: "Pecharunt", category: "Mythical" }
    ]
  }
];
const SlantedAccordion = ({ name, category, description, backgroundImage, gifPath, isActive, onToggle, imageClassName = "bg-cover" }) => {
  const [gifExists, setGifExists] = useState(true);
  const activeHeight = (gifPath && gifExists) ? 'h-[500px]' : 'h-72';
  
  return (
    <div className={`transition-all duration-500 ease-in-out -mt-[2px] first:mt-0 relative ${isActive ? 'w-full z-30' : 'w-[85%] z-10 hover:z-20'}`}>
      <div 
        className="relative z-10 w-full bg-gray-500 p-[2px] transition-all duration-500" 
        style={{ clipPath: 'polygon(0 0, 100% 0, calc(100% - 60px) 100%, 0 100%)' }}
      >
        <div 
          onClick={onToggle}
          className={`relative bg-white group cursor-pointer overflow-hidden w-full transition-all duration-500 ease-in-out ${isActive ? activeHeight : 'h-40'}`}
          style={{ clipPath: 'polygon(0 0, 100% 0, calc(100% - 60px) 100%, 0 100%)' }}
        >
          {/* Background Image (left side stays anchored, right side expands, opacity fades) */}
          <div className={`absolute inset-y-0 left-64 overflow-hidden transition-all duration-700 ease-in-out ${isActive ? 'right-0 opacity-15' : 'right-32 opacity-100'}`}>
            <div 
              className={`absolute inset-0 bg-center transition-transform duration-700 ease-in-out ${isActive ? '' : 'group-hover:scale-105'} ${imageClassName}`}
              style={{ backgroundImage: `url(${backgroundImage || '/' + name.toLowerCase() + '.png'})` }}
            />
          </div>

          {/* Gradient overlay */}
          <div className={`absolute inset-0 bg-gradient-to-r from-gray-950 via-gray-900/80 to-transparent pointer-events-none transition-opacity duration-500 ${isActive ? 'opacity-0' : 'opacity-100'}`} />

          {/* Smooth Absolute Animation Container */}
          <div className="absolute inset-0 w-full h-full pointer-events-none">
            
            {/* Title Section */}
            <div className={`absolute left-10 transition-all duration-500 flex flex-col gap-1 w-64 pointer-events-auto ${isActive ? 'top-10 translate-y-0' : 'top-1/2 -translate-y-1/2'}`}>
              <span className={`text-xs uppercase tracking-widest font-bold transition-colors duration-500 ${isActive ? 'text-blue-600' : 'text-blue-400'}`}>{category}</span>
              <h3 className={`text-5xl font-black tracking-tighter transition-colors duration-500 ${isActive ? 'text-gray-900' : 'text-white'}`}>{name}</h3>
            </div>
            
            {/* Expanded Content (Text and GIF stacked) */}
            <div className={`absolute left-80 right-32 top-10 flex flex-col gap-6 transition-all duration-500 ${isActive ? 'opacity-100 translate-x-0 pointer-events-auto delay-100' : 'opacity-0 translate-x-10 pointer-events-none'}`}>
              <div className="max-w-3xl">
                <h4 className="text-2xl font-bold text-gray-800 mb-3">Details & Effects</h4>
                <p className="text-gray-700 whitespace-pre-line text-lg leading-relaxed">
                  {description || "Move description and effects are currently pending."}
                </p>
              </div>
              
              {(gifPath && gifExists) && (
                <div className="w-80 shrink-0 bg-white/50 backdrop-blur-sm rounded-xl border border-gray-300 p-2 shadow-sm">
                  <img 
                    src={gifPath} 
                    alt={`${name} mechanic`} 
                    className="w-full rounded-lg" 
                    onError={() => setGifExists(false)}
                  />
                </div>
              )}
            </div>

            {/* Toggle Button */}
            <div className={`absolute transition-all duration-500 flex flex-col items-center gap-2 pointer-events-auto ${isActive ? 'top-10 right-20 text-gray-500 hover:text-gray-900' : 'top-1/2 -translate-y-1/2 right-16 text-white hover:text-blue-300'}`}>
              <span className="text-sm font-semibold uppercase tracking-wider">{isActive ? 'Close' : 'View'}</span>
              {isActive ? <ChevronUp size={36} strokeWidth={2.5}/> : <ChevronDown size={36} strokeWidth={2.5} />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const RegionDivider = ({ region }) => (
  <div className="flex items-center w-full mt-10 mb-4 px-2">
    <h3 className="text-xl font-bold text-gray-500 uppercase tracking-widest mr-6">{region}</h3>
    <div className="flex-grow h-px bg-gray-400"></div>
  </div>
);

const ViewHome = () => (
  <div className="max-w-3xl px-6 mt-10">
    <h1 className="text-5xl font-extrabold text-gray-950 mb-6 tracking-tighter">Pokémon Desktop Engine</h1>
    <p className="text-xl text-gray-800 leading-relaxed mb-4">
      This is the internal documentation for the custom, physics-based desktop pet engine. 
      It details entity-specific states, visual techniques, and user interaction mechanics.
    </p>
  </div>
);

const ViewLegendaries = () => {
  const [activeAccordion, setActiveAccordion] = useState(null);

  return (
    <div className="max-w-[1400px]">
      <h2 className="text-3xl font-bold text-gray-900 mb-2 border-b-2 border-gray-300 pb-2 ml-10">Legendary & Mythical Roster</h2>
      <p className="text-gray-600 mb-10 ml-10 max-w-2xl">This list isolates all entities currently mapped in the engine, providing access to their specific abilities and effects.</p>
      
      {ROSTER_DATA.map((generation) => (
        <div key={generation.region}>
          <RegionDivider region={generation.region} />
          <div className="w-full border-t border-gray-300 bg-transparent">
            {generation.entities.map((pokemon) => (
              <SlantedAccordion 
                key={pokemon.name}
                name={pokemon.name}
                category={pokemon.category}
                isActive={activeAccordion === pokemon.name}
                onToggle={() => setActiveAccordion(activeAccordion === pokemon.name ? null : pokemon.name)}
                backgroundImage={`/${pokemon.name.toLowerCase().replace(/[:\s]/g, '')}.png`}
                gifPath={`/${pokemon.name.toLowerCase().replace(/[:\s]/g, '')}.gif`}
                description={pokemon.description}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const TYPE_DATA = [
  { name: "Normal", category: "Type" },
  { name: "Fire", category: "Type" },
  { name: "Water", category: "Type" },
  { name: "Grass", category: "Type" },
  { name: "Electric", category: "Type" },
  { name: "Ice", category: "Type" },
  { name: "Fighting", category: "Type" },
  { name: "Poison", category: "Type" },
  { name: "Ground", category: "Type" },
  { name: "Flying", category: "Type" },
  { name: "Psychic", category: "Type" },
  { name: "Bug", category: "Type" },
  { name: "Rock", category: "Type" },
  { name: "Ghost", category: "Type" },
  { name: "Dragon", category: "Type" },
  { name: "Dark", category: "Type" },
  { name: "Steel", category: "Type" },
  { name: "Fairy", category: "Type" }
];

const ViewTypes = () => {
  const [activeAccordion, setActiveAccordion] = useState(null);

  return (
    <div className="max-w-[1400px]">
      <h2 className="text-3xl font-bold text-gray-900 mb-2 border-b-2 border-gray-300 pb-2 ml-10">Type Mechanics</h2>
      <p className="text-gray-600 mb-10 ml-10 max-w-2xl">Detailed logic for each type class (e.g., Ghost-type phasing, Flying-type gravity override) is documented here.</p>
      
      <div>
        <RegionDivider region="All Types" />
        <div className="w-full border-t border-gray-300 bg-transparent">
          {TYPE_DATA.map((type) => (
            <SlantedAccordion 
              key={type.name}
              name={type.name}
              category={type.category}
              isActive={activeAccordion === type.name}
              onToggle={() => setActiveAccordion(activeAccordion === type.name ? null : type.name)}
              backgroundImage={`/${type.name.toLowerCase()}.svg`}
              gifPath={`/${type.name.toLowerCase()}.gif`}
              imageClassName={`bg-[length:100px] bg-no-repeat opacity-80 ${activeAccordion === type.name ? 'scale-[2]' : 'scale-100'}`}
              description="Type specific effects and passive mechanics are currently pending."
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const ViewAbout = () => (
  <div className="max-w-3xl px-10 py-6 mt-10">
    <h2 className="text-3xl font-bold text-gray-900 mb-6">About the Architecture</h2>
    <p className="text-lg text-gray-700 mb-4">The core engine operates on Python utilizing Tkinter. It relies on an asynchronous physical loop updating at 50ms intervals to handle body logic and visual rendering concurrently.</p>
  </div>
);

export default function App() {
  const [activeTab, setActiveTab] = useState('legendaries'); 

  const renderView = () => {
    switch (activeTab) {
      case 'home': return <ViewHome />;
      case 'legendaries': return <ViewLegendaries />;
      case 'types': return <ViewTypes />;
      case 'about': return <ViewAbout />;
      default: return <ViewHome />;
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans pb-20 relative">
      
      {/* Background Tech Element */}
      <div className="fixed bottom-0 right-0 w-[450px] h-[450px] pointer-events-none z-0 opacity-40">
        <svg viewBox="0 0 400 400" className="w-full h-full text-gray-400" fill="none" xmlns="http://www.w3.org/2000/svg">
          
          {/* Tech Lines from Right */}
          <path d="M 400 100 L 250 100 L 170 20" stroke="currentColor" strokeWidth="2" />
          <circle cx="250" cy="100" r="4" fill="currentColor" />
          <circle cx="170" cy="20" r="6" stroke="currentColor" strokeWidth="2" fill="white" />
          
          <path d="M 400 200 L 280 200 L 150 70" stroke="currentColor" strokeWidth="3" />
          <circle cx="280" cy="200" r="4" fill="currentColor" />
          <circle cx="150" cy="70" r="8" stroke="currentColor" strokeWidth="3" fill="white" />
          <circle cx="150" cy="70" r="3" fill="currentColor" />

          {/* Tech Line from Bottom */}
          <path d="M 150 400 L 150 280 L 30 160" stroke="currentColor" strokeWidth="3" />
          <circle cx="150" cy="280" r="4" fill="currentColor" />
          <circle cx="30" cy="160" r="8" stroke="currentColor" strokeWidth="3" fill="white" />
          <circle cx="30" cy="160" r="3" fill="currentColor" />

          {/* Stylized Pokeball - Center at 330, 330, radius 45 */}
          <g transform="translate(330, 330)" stroke="currentColor">
            {/* Top half filled */}
            <path d="M -45 0 A 45 45 0 0 1 45 0 Z" fill="currentColor" strokeWidth="6" />
            {/* Bottom half outline */}
            <path d="M -45 0 A 45 45 0 0 0 45 0" fill="none" strokeWidth="6" />
            {/* Middle bar */}
            <path d="M -45 0 H -15 M 15 0 H 45" strokeWidth="6" />
            {/* Center button */}
            <circle cx="0" cy="0" r="12" fill="white" strokeWidth="6" />
          </g>
        </svg>
      </div>

      <nav className="bg-gradient-to-r from-gray-950 to-black text-white shadow-xl sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-4">
          <div className="flex space-x-1">
            {['home', 'legendaries', 'types', 'about'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-8 py-5 font-bold text-sm uppercase tracking-widest transition-colors border-b-4 ${
                  activeTab === tab 
                    ? 'border-blue-500 text-white bg-white/10' 
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="mx-auto py-12 relative z-10">
        {renderView()}
      </main>
      
    </div>
  );
}