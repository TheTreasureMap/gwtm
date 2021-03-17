/*
    GWTM Aladin Visualization javascript controller

    I am in no way a javascript master
    This is entirely self-taught masochism that I do not wish
        upon anyone.
    Please do not try to implement this. 
    If you do: please follow along with the static/templates/alert_info.html file
    there is a lot of global variable manipulation going on here, not suggested.

    It only functions by the grace of god and aderall.

    -Samuel Wyatt 2021
*/

/*
    Function to initialize the GWTM aladin interface
    Needs to incorporate markers.
*/
function gwtmAladinInit(data) {
    var fov = 180;

    var aladinParams = {
        fov: fov, 
        target: data.target_init, 
        showGotoControl:true, 
        showFullscreenControl: true, 
        showSimbadPointerControl: true, 
        showShareControl: true, 
        realFullscreen: false, 
        cooFrame:"ICRSd", 
        showReticle: false
    };

    if ('aladin' in data){
        var aladin = data.aladin;
    }
    else {
        var aladin = A.aladin('#aladin-lite-div', aladinParams);
    }
    
    aladin_setImage(aladin, 'static/sun-logo-100.png', 'Sun at GW T0', data.sun_ra, data.sun_dec)
    aladin_setImage(aladin, 'static/moon-supersmall.png', 'Moon at GW T0', data.moon_ra, data.moon_dec)

    var detectionoverlaylist = aladin_setContours(aladin, data.detection_overlays)
    var instoverlaylist = aladin_setContours(aladin, data.inst_overlays)
    var grboverlaylist = aladin_setMOC(aladin, data.GRBoverlays)

    aladin_drawInstHTML(data.inst_overlays, 'alert_instruments_div')
    aladin_drawGRBHTML(data.GRBoverlays, 'alert_grbcov_div')

    var ret = {
        aladin: aladin,
        detectionoverlaylist: detectionoverlaylist,
        instoverlaylist: instoverlaylist,
        grboverlaylist: grboverlaylist
    }

    return ret;
};

/*
    not sure if this works. Didn't delete
*/
$('input[name=survey]').change(function() {
    aladin.setImageSurvey($(this).val());
});

/*
    draws an image onto the aladin viz interface
*/
function aladin_setImage(
    aladin,
    imgsource,
    imgname,
    pos_ra, pos_dec
){
    var IMG = new Image();
    IMG.src = imgsource;
    var cat = A.catalog({shape: IMG, name: imgname})
    aladin.addCatalog(cat);
    cat.addSources(A.source(pos_ra, pos_dec))
};

/*
    draws a MOC map on the aladin interface
    returns the overlay list to memory so it can be remembered on event redraw
*/
function aladin_setMOC(
    aladin,
    moc_list
){
    moc_overlayList=[];
    for (i = 0; i < moc_list.length; i++) {
        var moc = A.MOCFromJSON(moc_list[i].json, {opacity: 0.25, color: moc_list[i].color, lineWidth: 1, name: moc_list[i].name});
        aladin.addMOC(moc);
        moc_overlayList[i] = moc;
        moc.hide()
    }
    return moc_overlayList
}

/*
    function to draw contours on the aladin viz
*/
function aladin_setContours(
    aladin, 
    contour_list,
){
    overlaylist = [];
    for (i = 0; i < contour_list.length; i++) {
        var contour = A.graphicOverlay({id: i, color:contour_list[i].color, lineWidth: 2, name:contour_list[i].name});
        aladin.addOverlay(contour);
        var overlay_contours = contour_list[i].contours
        for (j = 0; j < overlay_contours.length; j++){
            contour.addFootprints([A.polygon(overlay_contours[j].polygon)])
        }
        overlaylist[i] = {
            'contour':contour,
            'toshow':true,
            'tocolor':contour_list[i].color
        }
    }
    return overlaylist
}

/*
    function to draw markers on the aladin viz
*/
function aladin_setMarkers(
    aladin,
    marker_list
) {
    set_marker_list = []
    for (i = 0; i < marker_list.length; i++) {
        var groupname = marker_list[i].name
        var markers = marker_list[i].markers
        var markerlayer = A.catalog({name:groupname})
        for (j = 0; j < markers.length; j++) {
            var marker = A.marker(markers[j].ra, markers[j].dec, {popupTitle: markers[j].name, popupDesc: markers[j].info})
            markerlayer.addSources([marker])
        }
        aladin.addCatalog(markerlayer)

        set_marker_list[i] = {
            'name':groupname,
            'markerlayer': markerlayer
        }
    }
    return set_marker_list
}

/*
    Function that redraws the instrument contours based on the pointing time
    the slidervals come from the timeslider ui
*/
function aladin_sliderRedrawContours(
    aladin, 
    input_contour_list,
    set_contour_list,
    slidervals
) {
    mint = slidervals.mint
    maxt = slidervals.maxt

    for (i = 0; i < input_contour_list.length; i++) {
        var toshow = false
        var tocolor = ''
        var iter = 0
    
        for (j = 0; j < set_contour_list.length; j++) {
            if (input_contour_list[i].name == set_contour_list[j].contour.name) {
                toshow = set_contour_list[j].toshow; 
                tocolor = set_contour_list[j].tocolor; 
                iter = j
            }
        }
        
        var contour = A.graphicOverlay({id: i, color:tocolor, lineWidth: 2, name:input_contour_list[i].name});
        aladin.addOverlay(contour);
        var overlay_contours = input_contour_list[i].contours
        for (j = 0; j < overlay_contours.length; j++){
            if (overlay_contours[j].time >= mint && overlay_contours[j].time <= maxt){
                contour.addFootprints([A.polygon(overlay_contours[j].polygon)])
            }
            if (!toshow) { 
                contour.hide() 
            }
        }
        set_contour_list[iter].contour = contour
    }
    return set_contour_list
}

function aladin_removeContour(
    contouroverlaylist
) {
    for (i = 0; i < contouroverlaylist.length; i++) {
        contouroverlaylist[i].contour.removeAll()
    }
    aladin.view.requestRedraw();
}

/*
    Hides or shows an overlay from the checkbox
*/
function aladin_overlayToggleOne(
    target,
    overlay_list
) {
    var iter = 0
    for(var k=0; k<overlay_list.length; k++)
    {
        if (target.id == overlay_list[k].contour.name) {
            iter = k
        }
    }
    if (target.checked) {
        overlay_list[iter].contour.show()
        overlay_list[iter].toshow = true
    }
    else {
        overlay_list[iter].contour.hide()
        overlay_list[iter].toshow = false
    }
    aladin.view.requestRedraw();
}

/*
    Toggles all contours on the aladin viz
    toShow = True : show all
    toShow = False: hide all
*/
function aladin_overlayToggleAll(
    overlay_list, 
    toShow
) {
    for(var k=0; k<overlay_list.length; k++)
    {
        overlay_list[k].toshow = toShow
        if (toShow) {
            overlay_list[k].contour.show()
        }
        else {
            overlay_list[k].contour.hide()
        }
    }
    aladin.view.requestRedraw();
    return overlay_list
  }

/*
    Hides or shows the MOC from checkbox
*/
function aladin_mocToggleOne(
    target,
    moc_list
) {
    var iter = 0
    for(var k=0; k<moc_list.length; k++)
    {
        if (target.id == moc_list[k].name) {
        iter = k
        }
    }
    if (target.checked) {
        moc_list[iter].show()
    }
    else {
        moc_list[iter].hide()
    }
    aladin.view.requestRedraw();
}

/*
    Toggles all MOC overlays on the aladin viz
    toShow = True : show all
    toShow = False: hide all
*/
function aladin_mocToggleAll(
    moc_list,
    toShow
) {
    for(var k=0; k<moc_list.length; k++)
    {
        if (toShow) {
            moc_list[k].show()
        }
        else {
            moc_list[k].hide()
        }
    }
    aladin.view.requestRedraw()
}

/*
    Toggles all markers on the aladin viz
    toShow = True : show all
    toShow = False: hide all
*/
function aladin_markerToggleAll(
    marker_list,
    toShow
) {
    for (var i = 0; i < marker_list.length; i++) {
        markerlayer = marker_list[i].markerlayer
        if (toShow) {
            markerlayer.show() 
        }
        else { 
            markerlayer.hide() 
        }
    }
}

/*
    Draws the html on the side of the aladin interface
    with the given html div-tid
*/
function aladin_drawInstHTML(
    overlay_list,
    div_name,
) {
    var overlayhtml = '<ul style="list-style-type:none;">'
    for (var k=0 ; k<overlay_list.length; k++) {
        var cat = overlay_list[k];
        overlayhtml += '<li><div>';
        overlayhtml += '<fieldset><label for="' + cat.name + '" style="display: inline-block;">';
        overlayhtml += '<input id="' + cat.name + '" type="checkbox" value="' + cat.name + '" checked="checked" style="display: inline-block;">';// + cat.name + ' </input>';
        overlayhtml += '<div class="overlaycolorbox" style="background-color: '+cat.color+';"></div><span>'+cat.name+'</span></input></label>';
        //overlayhtml += '<input id="' + cat.name + '" type="checkbox" value="' + cat.name + '" checked="checked">';
        //overlayhtml += '<div class="overlaycolorbox" style="background-color: '+cat.color+';"></div><span>' + cat.name + '</span></input></label>';
        overlayhtml += '</fieldset></div></li>';
    }   
    overlayhtml += '</ul>';
    $('#'+div_name).html(overlayhtml)
}

/*
    Draws the HTML for the GRB MOC list
    includes a checkbox to toggle visibility
*/
function aladin_drawGRBHTML(
    grboverlay_list,
    div_name
) {
    var GRBhtml = '<ul style="list-style-type:none;">'
    for (var k=0 ; k<grboverlay_list.length; k++) {
        var cat = grboverlay_list[k];
        if (cat.name == 'Fermi in South Atlantic Anomaly'){
            GRBhtml += '<li><fieldset><label for="' + cat.name + '">' + cat.name + '</label>';
            GRBhtml += '</fieldset></li>';
        } else {
            GRBhtml += '<li><div><fieldset><label for="' + cat.name + '" style="display: inline-block;">';
            GRBhtml += '<input id="' + cat.name + '" type="checkbox" value="' + cat.name + '" style="display: inline-block;">';// + cat.name + ' </input>';
            GRBhtml += '<div class="overlaycolorbox" style="background-color: '+cat.color+';"></div><span>'+cat.name+'</span></input></label>';
            //GRBhtml += '<input id="' + cat.name + '" type="checkbox" value="' + cat.name + '" style="display: inline-block;">';
            //GRBhtml += '<div class="overlaycolorbox" style="background-color: '+cat.color+';"></div><span>' + cat.name + '</span></input></label>'
            GRBhtml += '</fieldset></div></li>';
        }
    }
    GRBhtml += '</ul>'
    $('#'+div_name).html(GRBhtml);
}

/*
    Draws the HTML for the Sources Marker list
    includes a collapsible list for each collection of markers
*/
function aladin_setMarkerHtml(
    marker_list,
    marker_div,
) {
    var html = '<ul style="list-style-type:none;">'
    for (i = 0; i < marker_list.length; i++) {
        var groupname = marker_list[i].name
        var idstr = groupname.replace(/\s+/g, '')
        html += '<li>'
        html += '<button id="collbtn'+idstr+'" onclick="changeCollapseButtonText(this.id)" type="button" class="btn btn-primary btn-xs right-triangle" data-toggle="collapse" data-target="#'+idstr+'"></button>';
        html += '<p style="display: inline-block"> '+groupname+'</p>'
        html += '<div class="collapse scroll-section" id="'+idstr+'">'
        var markers = marker_list[i].markers
        for (j = 0; j < markers.length; j++) {
            markername = markers[j].name
            html += '<fieldset ><label for="' + markername+ '">';
            html += '<p id="' + markername+ '" type="text" value="' + markername + '" >' + markername + '</p></label>';
            html += '</fieldset>';
        } 
        html += '</div>'
        html += '</li>'
    }
    html += '</ul>'
    $('#'+marker_div).html(html);
}

/*
    When the user clicks on a source in the collapsible list
    it will animate the aladin vizualization and move to that source
*/
function aladin_animateToMarker(
    target, 
    inputmakerlist
) {
    for (i = 0; i < inputmakerlist.length; i++) {
      var gal_markers = inputmakerlist[i].markers
      for (j = 0; j < gal_markers.length; j++) {
        if (target.id == gal_markers[j].name) {
          var ra = gal_markers[j].ra;
          var dec = gal_markers[j].dec;
          aladin.zoomToFoV(3,3)
          aladin.animateToRaDec(ra, dec, 3);
        }
      }
    }
}

/*
    Changes the color of an instrument overlay
    Doesn't work right now
*/
$('.indicator').click(function() {
    var $this = $(this);
    if ($this.hasClass('right-triangle')) {
        $this.removeClass('right-triangle');
        $this.addClass('down-triangle');
        $this.parent().find('.cat-options').slideDown(300);
        var hipsId = $(this).parent().find("input[type='checkbox']").val();
        var iter = 0
        for(var k=0; k<instoverlaylist.length; k++)
        {
          if (hipsId == instoverlaylist[k][0].name) {
            iter = k
          }
        }
        $this.parent().find("input[type='color']").val(instoverlaylist[iter][0].color);
    }
    else {
        $this.removeClass('down-triangle');
        $this.addClass('right-triangle');
        $this.parent().find('.cat-options').slideUp(300);
    }
});

/*
    Function that listens to the time slider. 
    clears the visualization and redraws the contours
    considers the time of the instrument pointings 
    will not redraw markers... YET
*/
$(function() {
    $( "#slider-range" ).slider({
        range: true,
        min: slider_min,
        max: slider_max,
        step: slider_step,
        values: slider_vals,

        slide: function( event, ui ) {
            slidervals = {
                mint : new Number(ui.values[0]),
                maxt : new Number(ui.values[1])
            }
            
            $("#amount").val((slidervals.mint).toFixed(3) + " - " + (slidervals.maxt).toFixed(3));
            aladin.removeLayers()
            
            aladin_setImage(aladin, 'static/sun-logo-100.png', 'Sun at GW T0', data.sun_ra, data.sun_dec)
            aladin_setImage(aladin, 'static/moon-supersmall.png', 'Moon at GW T0', data.moon_ra, data.moon_dec)
            
            grboverlaylist = aladin_setMOC(aladin, data.GRBoverlays)
            instoverlaylist = aladin_sliderRedrawContours(aladin, data.inst_overlays, instoverlaylist, slidervals)
            detectionoverlaylist = aladin_setContours(aladin, data.detection_overlays)

            //place holder fix for Sources. 
            $('#alert_gal_div').html('');
            var button = document.getElementById('alert_event_galaxies');
            button.innerHTML = 'Get'

            $('#alert_scimmadiv').html('');
            var button = document.getElementById('alert_scimma_xrt');
            button.innerHTML = 'Get'
        }
  });
  $( "#amount" ).val( (new Number($( "#slider-range" ).slider( "values", 0 ))) +
    " - " + (new Number($( "#slider-range" ).slider( "values", 1 ))));
});