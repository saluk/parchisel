class TextureCache {
  constructor(stage) {
    this.stage = stage;
    this.store = {};
  }
  async getOrAddTexture(url){
    if(this.store[url]) {
      return this.store[url];
    }
    const texture = await PIXI.Assets.load(url);
    this.store[url] = texture;
    return texture;
  }
}

class Point {
  constructor(x, y) {
    this.x = x;
    this.y = y;
  }
}

class Graphic {
  constructor(texture) {
    this.sprite = new PIXI.Sprite(texture);
  }
}

class Card {
  constructor(point, vtId, graphic) {
    this.point = point;
    this.to_point = point;
    this.interp = true;
    this.vtId = vtId;
    this.graphic = graphic
    this.graphic.eventMode = 'static'
    // Center the sprite's anchor point
    this.graphic.anchor.set(0.5);
    this.app.stage.addChild(this.graphic);
  }
  applyHandler(user){
    this.graphic.on('pointerdown', (event)=>{user.onClickDown(event, this)});
    this.graphic.on('pointerup', (event)=>{user.onClickUp(event, this)})
    this.graphic.on('pointerupoutside', (event)=>{user.onClickUpOutside(event, this)})
  }
  tick(time){
    this.graphic.rotation += 0.1 * time.deltaTime;
    if(this.interp) {
      this.point.x += (this.to_point.x-this.point.x)/(10.0 * time.deltaTime);
      this.point.y += (this.to_point.y-this.point.y)/(10.0 * time.deltaTime);
      var closex = false;
      var closey = false;
      if(Math.abs(this.to_point.x-this.point.x)<1){
        this.point.x == this.to_point.x;
        closex = true;
      }
      if(Math.abs(this.to_point.y-this.point.y)<1){
        this.point.y == this.to_point.y;
        closey = true;
      }
      if(closex && closey) {
        this.interp = false;
      }
    }
    this.graphic.x = this.point.x;
    this.graphic.y = this.point.y;
  }
}

class User {
  constructor() {
    this.held = null;   // Held object doesn't receive inputs from the network, other users can't hold it
  }
  applyHandler(stage, application){
    stage.on('globalpointermove', (event)=>{if(this.held) {application.moveBunny(event, this.moving)}})
  }
  onClickDown(event, card) {
    if(!this.held){
      this.held = card;
    }
  }
  onClickUp(event, card) {
    if(this.held===card){
      this.held = null;
    }
  }
  onClickUpOutside(event, card){
    return this.onClickUp(event, card)
  }
}

class Scene {
  constructor() {
    this.cards = [];
    this.user = new User();
    this.textureCache = new TextureCache();
  }
  addCard(point, textureUrl, vtId) {
    const graphic = Graphic(this.textureCache.getOrAddTexture(textureUrl));
    const card = new Card(point, vtId, graphic);
    this.cards.push(card);
    card.applyHandler(this.user);
  }
  tick(time) {
    for(card of this.cards){
      card.tick(time)
    }
  }
  applyHandler(app){
    app.ticker.add(time=>{this.tick(time)})
  }
}

export default {
    template: `
        <div></div>
    `,
    props: {
      width: Number,
      height: Number
    },

    /**
     * How to create the client interface
     */
    async mounted() {
      
      // Create a new application
      this.app = new PIXI.Application();

      // Initialize the application
      await this.app.init({ background: '#000000', width: this.width, height: this.height });

      // Append the application canvas to the document body
      //document.body.appendChild(app.canvas);
      this.$el.appendChild(this.app.canvas);

      // Load a background
      // TODO localhost should be whatever the hostname is
      this.background_texture = await PIXI.Assets.load('http://127.0.0.1:6812/images/henrik-donnestad-t2Sai-AqIpI-unsplash.jpg');
      this.background = new PIXI.Sprite(this.background_texture);
      this.app.stage.addChild(this.background);
      // Load the bunny texture
      this.texture = await PIXI.Assets.load('https://pixijs.com/assets/bunny.png');

      this.scene = new Scene()
      this.scene.applyHandler(this.app)
      this.user = new User()
      this.user.applyHandler(this.app.stage, this)

      // drag to scroll stage
      this.clickrect = new PIXI.Graphics()
        .rect(0, 0, this.width, this.height);
      this.app.stage.addChild(this.clickrect);
      this.dragstage = null;
      this.app.stage.on('pointerdown', (event)=>{this.dragstage = this.app.stage});
      this.app.stage.on('globalpointermove', (event)=>{if(this.dragstage && !this.user.held) {
        this.app.stage.x += event.movement.x;
        this.app.stage.y += event.movement.y;
        this.clickrect.clear();
        this.clickrect.rect(
          -this.app.stage.x/this.app.stage.scale.x, 
          -this.app.stage.y/this.app.stage.scale.y, 
          this.width/this.app.stage.scale.x, 
          this.height/this.app.stage.scale.y
        );
        this.app.stage.hitArea = new PIXI.Rectangle(
          -this.app.stage.x/this.app.stage.scale.x, 
          -this.app.stage.y/this.app.stage.scale.y, 
          this.width/this.app.stage.scale.x, 
          this.height/this.app.stage.scale.y
        );
      }});
      this.app.stage.on('pointerup', (event)=>{if(this.dragstage) {this.dragstage = null}});
      this.app.stage.on('pointerupoutside', (event)=>{if(this.dragstage) {this.dragstage = null}});
      this.app.stage.on('wheel', (event)=>{
        this.app.stage.scale.x -= event.deltaY / 1000.0;
        this.app.stage.scale.y -= event.deltaY / 1000.0;
        this.clickrect.clear();
        this.clickrect.rect(
          -this.app.stage.x/this.app.stage.scale.x, 
          -this.app.stage.y/this.app.stage.scale.y, 
          this.width/this.app.stage.scale.x, 
          this.height/this.app.stage.scale.y
        );
        this.app.stage.hitArea = new PIXI.Rectangle(
          -this.app.stage.x/this.app.stage.scale.x, 
          -this.app.stage.y/this.app.stage.scale.y, 
          this.width/this.app.stage.scale.x, 
          this.height/this.app.stage.scale.y
        );
        event.preventDefault();
      })
      this.app.stage.eventMode = 'static';
      this.app.stage.interactive = true;
      this.app.stage.hitArea = new PIXI.Rectangle(0, 0, this.width, this.height);
    },
    methods: {
      moveBunny(e, bunny) {
        bunny.point.x += e.movement.x;
        bunny.point.y += e.movement.y;
        this.$emit('newstate', this.getBunnyState());
      },
      getBunnyState() {
        var array = [];
        this.scene.cards.forEach(bunny => {
          array.push({"pos":[bunny.point.x, bunny.point.y], "id": bunny.vtid});
        });
        return array;
      },
      setBunnyState(state) {
        if(!this.scene){
          return;
        }
        state.forEach(bunny => {
          var obunny = this.scene.cards.find((item)=>{return item.vtid === bunny.vtid});
          if(obunny === undefined) {
            obunny = this.addBunny(bunny.point.x, bunny.point.y, bunny.vtid);
          } else {
            if(obunny===this.user.held){
              return;
            }
            // TODO some objects may not want interpolation
            obunny.interp = true;
            obunny.to_point.x = bunny.point.x;
            obunny.to_point.y = bunny.point.y;
          }
        });
      },
      addBunny(x, y, vtId) {
        // Create a bunny Sprite
        const bunny = this.scene.addCard(new Point(x,y), 'https://pixijs.com/assets/bunny.png', vtId)
        bunny.applyHandler(this.user)

        this.scene.cards.push(bunny);
        return bunny;
      }
    },
  };