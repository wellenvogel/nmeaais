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
        name: "userAisNearest",
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
        name: "userAisSelected",
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
    
    
    /* some styles to put into user.css
    .userAisNearest .infoRow,.userAisSelected .infoRow {
      text-align: left;
    }
    .userAisNearest .label,.userAisSelected .label{
      width: 6em;
    }
    */
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
      <iframe class="predict" src="${link}"/>
    </div>
    </div>`;
    }
    return rt;
  }
  var userAisSonde={
      name: "userAisSonde",
      caption: "AIS(sonde)",
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
        var launch_alt=undefined;
        if (current.destination && current.destination.match(/ALT=/)){
          var dv=parseFloat(current.destination.replace(/.*ALT= */,'').replace(/[^0-9.].*/,''));
          if (! isNaN(dv)){
            launch_alt=dv-props.altSub;
          }  
        }
        var timeBack=props.secondsBack*1000;
        var now=new Date();
        var launch_time=new Date(now.getTime()-timeBack).toISOString();
        var link=undefined;
        if (launch_alt !== undefined){
          if (launch_alt < 0) launch_alt=1000;
          if (this.lastAlt !== undefined && this.lastTime){
            var tdiff=now.getTime()-this.lastTime;
            var altDiff=launch_alt-this.lastAlt;
            var burstAlt=launch_alt-7;
            if (tdiff > 0){
              var downRate=altDiff*1000/tdiff;
              if (downRate < 1) downRate=7;
              link=`http://predict.cusf.co.uk/api/v1/?launch_latitude=${current.lat}&launch_longitude=${current.lon}&`+
              `launch_altitude=132.1&launch_datetime=${launch_time}&ascent_rate=15&burst_altitude=${burstAlt.toFixed(1)}&descent_rate=${downRate}`;
            }
          }
          this.lastTime=now.getTime();
          this.lastAlt=launch_alt;
        }
        return getSondeHtml(current,current.course,link);
      },
      storeKeys:{
        all:'nav.ais.list'
      }
  };
  var aisSondeUserParam={
    mmsi:{type:'NUMBER'},
    secondsBack:{type:'NUMBER',default: 3600},
    altSub:{type:'NUMBER',default: 40},
    unit:false
  };
  
  
  /* some styles to put into user.css
  .userAisSonde iframe.predict {
  width: 100%;
  height: 100%;
  }
  */
 avnav.api.registerWidget(userAisSonde,aisSondeUserParam);
 