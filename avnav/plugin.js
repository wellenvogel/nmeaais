/* widgets for the nearest AIS target and a selected one */ 
    
    /**
     *  helper to get the HTML, used for both widgets
    **/
    function getHtml(current,example){
    return `<div class="widgetData">
                <div class="infoRow">
                  <span class="label">mmsi:</span><span class="value">${current.mmsi}</span>
                </div>
                <div class="infoRow">
                  <span class="label">pos:</span><span class="value">${avnav.api.formatter.formatLonLats(current)}</span>
                </div>
                <div class="infoRow">
                  <span class="label">dist:</span><span class="value">${avnav.api.formatter.formatDistance(current.distance,'km')}</span>
                </div>
                <div class="infoRow">
                  <span class="label">course:</span><span class="value">${example}</span>
                </div>

              </div>`;
    }
    var userAisNearest={
        name: "sondeAisNearest",
        caption :"AIS(nearest)",
        renderHtml: function(props){
            var current=props.current;
            var example=current.course;
            //compute with example...                     
            return getHtml(current,example);
        },
        storeKeys:{
          current: 'nav.ais.nearest'
        }
    };
    var aisNearestUserParam={
      unit: false
    };
    /*
    *  a widget to show a particular MMSI
    *  in the layout editor you must input the mmsi
    */
    var userAisSelected={
        name: "sondeAisSelected",
        caption: "AIS(selected)",
        renderHtml: function(props){
          if (! props.all instanceof Array) return "<div>no AIS targets</div>";
          var current;
          for (var i=0;i<props.all.length;i++){
            if (props.all[i].mmsi == parseInt(props.mmsi)){
              current=props.all[i];
              break;
            }
          }
          if (! current) return `<div>mmsi ${props.mmsi} not found</div>`;
          return getHtml(current,current.course);
        },
        storeKeys:{
          all:'nav.ais.list'
        }
    };
    var aisSelectedUserParam={
      mmsi:{type:'NUMBER'},
      unit:false
    };
    
    
    avnav.api.registerWidget(userAisNearest,aisNearestUserParam);
    avnav.api.registerWidget(userAisSelected,aisSelectedUserParam);


    /*
    *  a widget to show a particular MMSI
    *  in the layout editor you must input the mmsi
    */
   function getSondeHtml(current,example,link){
    var rt=
  `<div class="widgetData">
  <div class="infoRow">
    <span class="label">mmsi:</span><span class="value">${current.mmsi}</span>
  </div>
  <div class="infoRow">
    <span class="label">pos:</span><span class="value">${avnav.api.formatter.formatLonLats(current)}</span>
  </div>
  <div class="infoRow">
    <span class="label">dist:</span><span class="value">${avnav.api.formatter.formatDistance(current.distance,'km')}</span>
  </div>
  <div class="infoRow">
    <span class="label">course:</span><span class="value">${example}</span>
  </div>`;
    if (link){
      rt+=`
    <div class="predictRow">
      <button onclick="click" class="predict" >Predict</button>
    </div>
    </div>`;
    }
    return rt;
  }
   var userAisSonde={
    name: "sondeAisPredict",
    caption: "AIS(predict)",
    renderHtml: function(props){
      if (! props.all instanceof Array) return "<div>no AIS targets</div>";
      var current;
      for (var i=0;i<props.all.length;i++){
        if (props.all[i].mmsi == parseInt(props.mmsi)){
          current=props.all[i];
          break;
        }
      }
      if (! current) return `<div>mmsi ${props.mmsi} not found</div>`;

      //compute parameters for the predict query
      var launch_alt=undefined; //the launch altitude
      if (current.destination && current.destination.match(/ALT=/)){
        var dv=parseFloat(current.destination.replace(/.*ALT= */,'').replace(/[^0-9.].*/,''));
        if (! isNaN(dv)){
          launch_alt=dv-props.altSub;
        }  
      }
      var timeBack=props.secondsBack*1000;
      var now=new Date();
      var launch_time=new Date(now.getTime()-timeBack).toISOString(); //the launch time
      var longitude=current.lon;
      var latitude=current.lat;
      var link=undefined;
      if (launch_alt !== undefined){
        if (launch_alt < 0) launch_alt=1000; //TODO: test
        //we can only compute the link if we already have previous
        //altitude and time values
        //they are stored at this.lastAlt and this.lastTime
        //if they are not set, the link is unset (and the button will not be shown)
        if (this.lastAlt !== undefined && this.lastTime){
          var tdiff=now.getTime()-this.lastTime;
          var altDiff=launch_alt-this.lastAlt;
          var burstAlt=launch_alt-7;
          if (tdiff > 0){
            var downRate=altDiff*1000/tdiff;
            if (downRate < 1) downRate=7; //TODO: test
            link=`http://predict.cusf.co.uk/api/v1/?launch_latitude=${latitude}&launch_longitude=${longitude}&`+
            `launch_altitude=132.1&launch_datetime=${launch_time}&ascent_rate=15&burst_altitude=${burstAlt.toFixed(1)}&descent_rate=${downRate}`;
            this.link=link; //store the link to be used later on in the button click
          }
        }
        //store the current values for the next computation
        this.lastTime=now.getTime();
        this.lastAlt=launch_alt;
      }
      return getSondeHtml(current,current.course,link);
    },
    initFunction: function(context){
      var frameId='aisSondeFrame';
      //we check if we already have the necessary object (an iframe) to show
      //the result. If not - create it now
      //context is the variable (object) that we can access using "this" in the renderHtml
      var displayFrame=document.getElementById(frameId);
      if (! displayFrame){
        //create the display elements as they are not there
        displayFrame=document.createElement('iframe');
        displayFrame.setAttribute('id',frameId);
        var wrapper=document.createElement('div');
        wrapper.setAttribute('id','aisSondeFrameWrapper');
        wrapper.addEventListener('click',function(){
          //when we click on the grey frame around the display we hide it
          displayFrame.classList.remove('visible');
        })
        wrapper.appendChild(displayFrame);
        //insert our display elemnt to the document
        document.body.appendChild(wrapper);
      }
      //remember our display frame
      context.displayFrame=displayFrame;
      //action for predict button click
      context.eventHandler.click=function(){
        if (context.displayFrame && context.link){
          //set the source of the display element to the last computed link
          context.displayFrame.src=context.link;
          //show the display
          context.displayFrame.classList.add('visible');
        }
      }
    },
    finalizeFunction:function(context){
      //if the widget goes away - just hide our display
      if (context.displayFrame) context.displayFrame.classList.remove('visible');
    },
    storeKeys:{
      all:'nav.ais.list'
    }
  };
    var aisSondeUserParam={
      mmsi:{type:'NUMBER'},
      secondsBack:{type:'NUMBER',default: 3600,description:'seconds back from now for launch time'}, 
      altSub:{type:'NUMBER',default: 40,description:'meters we subtract from current altitude'},
      unit:false
    };
    
 avnav.api.registerWidget(userAisSonde,aisSondeUserParam);
