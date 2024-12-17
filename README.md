# crazyflie_swarm

## Loco Positioning System

### General Informations

- [Loco Positioning System Doc](https://www.bitcraze.io/documentation/system/positioning/loco-positioning-system/)

#### Positioning modes
In questa sezione ci si riferisce a Anchor come il sistema che sta a terra (i Loco positioning Node) e a **Tag** con i sistemi che vengono tracciati dalle Anchor (che in genere sono i Loco positioning Deck nel caso di crazyflie, ma possono essere anche i Node se usati su robot più grandi)

- TWR:
  - 4/6 anchor
  - 1 crazyflie
  - non limita il movimento alla zona delimitata dalle anchor
  - è il più preciso
- **TDoA2**: 
  - 8 anchor
  - N crazyflie
  - è meglio se i crazyflie volano nella zona delmitata dalle anchor
  - con 8 anchor la precisione è comparabile con TWR
  - è la modalità più adatta per swarming
- TDoA3:
  - Simile a TDoA2, ma permette di aggionere ancora più anchors, il che significa che è possibile scalare il problema a spazi più grandi e anche con più stanze (Long Range Mode)

#### Performance
< 10cm di range. Dipende molto dal setup e dall'ambiente

#### System Components
- **Loco Positioning Deck**: crazyflife 2.X expansion deck con funzionalità di Loco Positioning Tag (può essere tracciato).
- **Loco Positiioning Node**: può essere usato sia come Anchor (per tracciare) che come Tag (per essere tracciato). In genere viene usato come Anchor.


### Getting Started
- [Getting Started With Loco Positioning System](https://www.bitcraze.io/documentation/tutorials/getting-started-with-loco-positioning-system/)

#### Firmware upgrading
[Upgrade Crazyflie Firmware](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/userguides/userguide_client/#firmware-upgrade)

