import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

// Data layer decoupled from UI. 
// Maintains the roster in Pokédex order while isolating descriptions from the render logic.
const ROSTER_DATA = [
  {
    region: "Kanto",
    entities: [
      { name: "Articuno", category: "Legendary" },
      { name: "Zapdos", category: "Legendary" },
      { name: "Moltres", category: "Legendary" },
      { name: "Mewtwo", category: "Legendary" },
      { name: "Mew", category: "Mythical" }
    ]
  },
  {
    region: "Johto",
    entities: [
      { name: "Raikou", category: "Legendary" },
      { name: "Entei", category: "Legendary" },
      { name: "Suicune", category: "Legendary" },
      { name: "Lugia", category: "Legendary" },
      { name: "Ho-Oh", category: "Legendary" },
      { name: "Celebi", category: "Mythical" }
    ]
  },
  {
    region: "Hoenn",
    entities: [
      { name: "Regirock", category: "Legendary" },
      { name: "Regice", category: "Legendary" },
      { name: "Registeel", category: "Legendary" },
      { name: "Latias", category: "Legendary" },
      { name: "Latios", category: "Legendary" },
      { name: "Kyogre", category: "Legendary" },
      { name: "Groudon", category: "Legendary" },
      { name: "Rayquaza", category: "Legendary" },
      { name: "Jirachi", category: "Mythical" },
      { name: "Deoxys", category: "Mythical" }
    ]
  },
  {
    region: "Sinnoh",
    entities: [
      { name: "Uxie", category: "Legendary" },
      { name: "Mesprit", category: "Legendary" },
      { name: "Azelf", category: "Legendary" },
      { name: "Dialga", category: "Legendary" },
      { name: "Palkia", category: "Legendary" },
      { name: "Heatran", category: "Legendary" },
      { name: "Regigigas", category: "Legendary" },
      { name: "Giratina", category: "Legendary" },
      { name: "Cresselia", category: "Legendary", description: "Flies to the top of your screen and covers the area in a glowing aurora. This light protects all pets, granting them temporary immunity so they cannot be grabbed, clicked, or moved by the user's cursor." },
      { name: "Phione", category: "Mythical" },
      { name: "Manaphy", category: "Mythical" },
      { name: "Darkrai", category: "Mythical", description: "Summons a dark void that acts as a gravity well, pulling in nearby pets. Once trapped, targets are forced into a nightmare state, putting them to sleep and leaving them completely immobilized until the void dissipates." },
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
      { name: "Reshiram", category: "Legendary", description: "Flies in a straight line across the screen at high speeds, leaving a trail of flames behind. Any pet that walks through this fire trail gets burned and has their movement speed drastically slowed down." },
      { name: "Zekrom", category: "Legendary" },
      { name: "Landorus", category: "Legendary" },
      { name: "Kyurem", category: "Legendary" },
      { name: "Keldeo", category: "Mythical" },
      { name: "Meloetta", category: "Mythical" },
      { name: "Genesect", category: "Mythical" }
    ]
  },
  {
    region: "Kalos",
    entities: [
      { name: "Xerneas", category: "Legendary" },
      { name: "Yveltal", category: "Legendary" },
      { name: "Zygarde", category: "Legendary" },
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
      { name: "Solgaleo", category: "Legendary" },
      { name: "Lunala", category: "Legendary" },
      { name: "Nihilego", category: "Ultra Beast" },
      { name: "Buzzwole", category: "Ultra Beast" },
      { name: "Pheromosa", category: "Ultra Beast" },
      { name: "Xurkitree", category: "Ultra Beast" },
      { name: "Celesteela", category: "Ultra Beast" },
      { name: "Kartana", category: "Ultra Beast" },
      { name: "Guzzlord", category: "Ultra Beast" },
      { name: "Necrozma", category: "Legendary" },
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
      { name: "Zacian", category: "Legendary" },
      { name: "Zamazenta", category: "Legendary" },
      { name: "Eternatus", category: "Legendary" },
      { name: "Kubfu", category: "Legendary" },
      { name: "Urshifu", category: "Legendary" },
      { name: "Zarude", category: "Mythical" },
      { name: "Regieleki", category: "Legendary" },
      { name: "Regidrago", category: "Legendary" },
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
      { name: "Koraidon", category: "Legendary" },
      { name: "Miraidon", category: "Legendary" },
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

const SlantedAccordion = ({ name, category, description, backgroundImage, gifPath, isActive, onToggle }) => {
  return (
    <div className="border-b border-gray-300 last:border-b-0 w-full">
      <div 
        onClick={onToggle}
        className="relative bg-white group cursor-pointer h-40 flex items-center overflow-hidden"
        style={{ clipPath: 'polygon(0 0, 100% 0, calc(100% - 60px) 100%, 0 100%)' }}
      >
        <div className="absolute inset-y-0 left-64 right-32 overflow-hidden">
          <div 
            className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
            style={{ backgroundImage: `url(${backgroundImage || `/${name.toLowerCase()}.png`})` }}
          />
        </div>

        <div className="absolute inset-0 bg-gradient-to-r from-gray-950 via-gray-900/80 to-transparent pointer-events-none z-0" />

        <div className="relative w-full h-full flex items-center justify-between px-10 z-10">
          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-blue-400 font-bold">{category}</span>
            <h3 className="text-5xl font-black text-white tracking-tighter">{name}</h3>
          </div>
          
          <div className="text-white pr-16 flex flex-col items-center gap-2 hover:text-blue-300 transition-colors">
            <span className="text-sm font-semibold uppercase tracking-wider">{isActive ? 'Close' : 'View'}</span>
            {isActive ? <ChevronUp size={36} strokeWidth={2.5}/> : <ChevronDown size={36} strokeWidth={2.5} />}
          </div>
        </div>
      </div>

      <div className={`overflow-hidden transition-all duration-300 ease-in-out bg-gray-50 w-[calc(100%-80px)] rounded-bl-xl rounded-br-xl ${isActive ? 'max-h-[1000px] border-l border-r border-b border-gray-300 shadow-md mb-8' : 'max-h-0 border-transparent mb-0'}`}>
        <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 flex flex-col gap-4">
            <h4 className="text-2xl font-bold text-gray-800">Move Details & Effects</h4>
            {/* Swapped technical fallback text for a simpler, functional placeholder */}
            <p className="text-gray-700 whitespace-pre-line text-lg leading-relaxed">
              {description || "Move description and effects are currently pending."}
            </p>
          </div>
          <div className="w-full bg-white rounded-xl border border-gray-200 flex items-center justify-center p-4 shadow-sm">
            {gifPath ? (
              <img src={gifPath} alt={`${name} mechanic`} className="max-w-full rounded-lg shadow-sm" />
            ) : (
              <div className="text-gray-400 py-28 text-center text-sm font-mono">[ASSET_MISSING]</div>
            )}
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
                gifPath={pokemon.name === "Darkrai" ? "/darkrai.gif" : undefined}
                description={pokemon.description}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const ViewTypes = () => (
  <div className="max-w-4xl px-10 py-6 mt-10">
    <h2 className="text-3xl font-bold text-gray-900 mb-8 pb-2 border-b-2 border-gray-300">Type Mechanics</h2>
    <p className="text-lg text-gray-700">Detailed logic for each type class (e.g., Ghost-type phasing, Flying-type gravity override) is documented here.</p>
  </div>
);

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
    <div className="min-h-screen bg-gray-200 text-gray-900 font-sans pb-20">
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

      <main className="mx-auto py-12">
        {renderView()}
      </main>
      
    </div>
  );
}