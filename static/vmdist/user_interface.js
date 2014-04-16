/* user_interface.js
 *
 * displays deployments with the most updated list from the sites
 * image-site deployments are displayed in a grid per image
 * red is undeployed and green is deployed, and clicking will change their states
 * all changes are sent after executing save to update sites with new deployments
 * progress wheel starts and then stops at callback from update
 */

var first_deployments; //first is the original d from first page load
var curr_deployments; //curr is the constantly updated d from site
var new_deployments; //new is the changing d from the user's input

var stop; //setInterval set to stop, stop is called when saving
var obj; //required to be global to disable site buttons while saving
var saving; //set at init() and save() to disable site buttons

var api;
var OPSURL = {"init":"/accounts/profile/jsonhandler/",
              "get_deployments":"/accounts/profile/jsonhandler/",
              "update":"/accounts/profile/jsonhandler/"};
var DATA = {"init":"init",
            "update":"update",
            "deployments":"deployments"};

// compares the current list of deployments gotten from the cloud site
// with the original deployments on this site
// if any have been deleted on the cloud site, they are taken off
// the original deployments and the user's new deployments on this site
function compare_deployments() {

    // sets curr to the most recent set of deployments from the site
    curr_deployments = obj.deployments[0];

    // checks if any original deployments have disappeared from the site
    for (image in first_deployments) {
        sites = first_deployments[image];
        for (i=0;i<sites.length;i++) {
            site = sites[i];
            // if sites are missing then it will remove the site from the original
            // and the user's new deployments
            if (curr_deployments[image].indexOf(site) < 0) {
                first_deployments[image].splice(i, 1);
                new_deployments[image].splice(i, 1);
            }
        }
    }

    // sets the user's new deployments to match the original deployments
    // it will not delete any of the sites that the user have already selected to deploy
    if (obj.init == "True") {
        new_deployments = {};
        for (image in first_deployments) {
            site_list = [];
            sites = first_deployments[image];
            for (i=0;i<sites.length;i++) {
                site = sites[i];
                site_list.push(site);
            }
            new_deployments[image] = site_list;
        }
    }

}

function tmp_print(deployments) {
    for (image in deployments) {
        console.log(image);
        sites = deployments[image];
        for (i=0;i<sites.length;i++) {
            console.log(sites[i]);
        }
    }
}

// displays the deployments with D3 with each image and the sites that it's deployed on
function display_deployments() {

    console.log("displaying...");

    data = obj.all;

    compare_deployments();

    // gets the total number of sites
    tmp = d3.keys(data[0]);
    var num_sites = data[0][tmp].length;

    document.getElementById("deployments").innerHTML = "";

    deployments = d3.select(".deployments")
        .append("div")
    .selectAll("div")
        .data(data).enter();

    deployment = deployments.append("p");

    deployment.append("p")
        //.style("width", "400px")
        //.style("height", "100px")
        //.style("float", "left")
        .text(function(d) {
            image = String(d3.keys(d));
            return image;
        } );

    for (i=0;i<num_sites;i++) {

        deployment.append("p2")
            //.style("text-indent", "50px")
            //.style("float", "left")
            .attr("site", function(d) {
                key = d3.keys(d);
                site = d[key][i];
                return site;
            } )
            .text(function (d) {
                // site text
                key = d3.keys(d);
                site = d3.select(this).attr("site")
                return site;
            } )
            //.style("width", "100px")
            .style("opacity", function(d) {
                if (saving == true) {
                    return .5;
                } else {
                    return 1;
                }
            } )
            .style("background-color", function(d) {
                site = d3.select(this).attr("site") // current site
                key = d3.keys(d); // current image
                // searches through deployed images list
                // if the current image is deployed onto that site,
                // the box will be green, and if not red
                for (dep in new_deployments) {
                    if (key == dep) {
                        sites = new_deployments[key];
                        for (var i=0;i<sites.length;i++) {
                            if (site == sites[i]) {
                                return "green";
                            }
                        }
                    }
                }
                return "red"
            } )
            .on("mouseover", function() {
                if (saving == false) {
                    this.style.opacity=0.5;
                }
            } )
            .on("mouseout", function() {
                if (saving == false) {
                    this.style.opacity=1;
                }
            } )
            .on("click", function (d) {
                if (saving == false) {
                    image = String(d3.keys(d));
                    site = d3.select(this).attr("site")
                    //console.log("clicked " + site + " on " + image);
                    // switches colors from red to green and back by clicking
                    // adds and removes from a modified list of deployments
                    if (d3.select(this).style("background-color") == "rgb(0, 128, 0)") {
                        this.style.background = "red";
                        i = new_deployments[image].indexOf(site);
                        new_deployments[image].splice(i, 1);
                    } else {
                        this.style.background = "green";
                        new_deployments[image].push(site);
                    }
                }
            } );
    }

}

// sends the user's new deployments to be added and deleted on the appropriate sites
function save() {

    // stops the loop so that it will not automatically get more updates
    stop_loop();
    loading();
    saving = true;
    document.getElementById("save").disabled = true;
    console.log("saving...");
    // display deployments so that it disables Save button and site buttons at the same time
    // however this requires obj to be a global variable
    // displays a saved state of deployments that will be sent
    obj.init = "False";
    display_deployments();
    // makes one final request for deployments manually
    // sends user's new deployments and the final current response of deployments from the site
    dep = {};
    dep['new_deployments'] = new_deployments;
    DATA['deployments'] = dep;
    api.request("update", "deployments");
    // waits 3 seconds before sending deployments
    // this is done so that the get_deployments request finishes before this is executed
    //setTimeout('api.request("update", "deployments")', 3000);

}

// displays the sidebar links to Deployments, Images, Sites, and Logout
function display_sidebar() {

    data = ["Deployments", "Images", "Sites", "Help", "Logout"];
    d3.select(".links")
        .append("div") //div
        .selectAll("div") //div
            .data(data)
        .enter().append("p") //p
            .text(function(d) { return d; })
            .on("mouseover", function() {
                this.style.textDecoration="underline";
                this.style.background="#ECECEC"
            } )
            .on("mouseout", function() {
                this.style.textDecoration="none";
                this.style.background="white";
            } )
            .on("click", function(d) {
                var href = window.location.href;
                if (d == "Deployments") {
                    window.location = href.replace(/profile\/.*$/, "profile/");
                } else if (d == "Images") {
                    window.location = href.replace(/profile\/.*$/, "profile/images/");
                } else if (d == "Sites") {
                    window.location = href.replace(/profile\/.*$/, "profile/sites/");
                } else if (d == "Help") {
                    window.location = href.replace(/profile\/.*$/, "profile/help/");
                } else if (d == "Logout") {
                    window.location = href.replace(/profile\/.*$/, "profile/logout/");
                }
            });

}

// user clicks the 'Stop Auto-Update' button to stop the 10 second loop update interval
function stop_loop() {
    console.log("stopping...");
    clearInterval(stop);
}

// function for progress wheel and its options
function loading() {

    var opts = {
        lines: 13, // The number of lines to draw
        length: 7, // The length of each line
        width: 4, // The line thickness
        radius: 10, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        color: '#000', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
    };

    var target = document.getElementById('spinner');
    var spinner = new Spinner(opts).spin(target);

}
