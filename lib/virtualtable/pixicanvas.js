export default {
    template: `
        <div></div>
    `,
    props: {
      width: Number,
      height: Number
    },
    async mounted() {
      
      // Create a new application
      this.app = new PIXI.Application();

      // Initialize the application
      await this.app.init({ background: '#000000', width: this.width, height: this.height });

      // Append the application canvas to the document body
      //document.body.appendChild(app.canvas);
      this.$el.appendChild(this.app.canvas);

      // Load a background
      this.background_texture = await PIXI.Assets.load('http://localhost:6812/images/henrik-donnestad-t2Sai-AqIpI-unsplash.jpg');
      this.background = new PIXI.Sprite(this.background_texture);
      this.app.stage.addChild(this.background);
      // Load the bunny texture
      this.texture = await PIXI.Assets.load('https://pixijs.com/assets/bunny.png');

      // cards are bunny's
      this.cards = [];
      this.moving = null;

      // drag to scroll stage
      this.clickrect = new PIXI.Graphics()
        .rect(0, 0, this.width, this.height);
      this.app.stage.addChild(this.clickrect);
      this.dragstage = null;
      this.app.stage.on('pointerdown', (event)=>{this.dragstage = this.app.stage});
      this.app.stage.on('globalpointermove', (event)=>{if(this.dragstage && !this.moving) {
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
        bunny.x += e.movement.x;
        bunny.y += e.movement.y;
        this.$emit('newstate', this.getBunnyState());
      },
      getBunnyState() {
        var array = [];
        this.cards.forEach(bunny => {
          array.push({"pos":[bunny.x, bunny.y], "id": bunny.vtid});
        });
        return array;
      },
      setBunnyState(state) {
        if(!this.cards){
          return;
        }
        state.forEach(bunny => {
          var obunny = this.cards.find((item)=>{return item.vtid === bunny.vtid});
          if(obunny === undefined) {
            obunny = this.addBunny(bunny.x, bunny.y, bunny.vtid);
            this.cards.push(obunny);
          } else {
            if(obunny===this.moving){
              return;
            }
            // TODO some objects may not want interpolation
            obunny.interp = true;
            obunny.to_x = bunny.x;
            obunny.to_y = bunny.y;
            //obunny.x = bunny.x;
            //obunny.y = bunny.y;
          }
        });
      },
      addBunny(x, y, vtid) {
        // Create a bunny Sprite
        const bunny = new PIXI.Sprite(this.texture);

        // Center the sprite's anchor point
        bunny.anchor.set(0.5);

        // Move the sprite to the center of the screen
        bunny.x = x;
        bunny.y = y;
        bunny.vtid = vtid;
        bunny.interp = false;
        bunny.to_x = 0;
        bunny.to_y = 0;
        console.log('added bunny');
        console.log(bunny);

        this.app.stage.addChild(bunny);

        // Listen for animate update
        this.app.ticker.add((time) =>
        {
            bunny.rotation += 0.1 * time.deltaTime;
            if(bunny.interp) {
              bunny.x += (bunny.to_x-bunny.x)/(10.0 * time.deltaTime);
              bunny.y += (bunny.to_y-bunny.y)/(10.0 * time.deltaTime);
              var closex = false;
              var closey = false;
              if(Math.abs(bunny.to_x-bunny.x)<1){
                bunny.x == bunny.to_x;
                closex = true;
              }
              if(Math.abs(bunny.to_y-bunny.y)<1){
                bunny.y == bunny.to_y;
                closey = true;
              }
              if(closex && closey) {
                bunny.interp = false;
              }
            }
        });

        bunny.on('pointerdown', (event)=>{this.moving = bunny});
        bunny.on('globalpointermove', (event)=>{if(this.moving===bunny) {this.moveBunny(event, this.moving)}})
        bunny.on('pointerup', (event)=>{if(this.moving) {this.moving = null}})
        bunny.on('pointerupoutside', (event)=>{if(this.moving) {this.moving = null}})
        bunny.eventMode = 'static';
        return bunny;
      }
    },
  };