/* message_handler.js
 *
 * initializes page and ImageServiceAPI
 * sends and receives JSON messages with operation and deployment data
 * POST message is sent to jsonhandler in views.py by HTTPUtils
 * obtains response in callback and filters it to correct operation
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

// initializes the appropriate operation
function init(op) {
    console.log("initializing ImageServiceAPI");
    api = new ImageServiceAPI();
    api.request(op, "init");
    // if init is on the main deployment page, it automatically makes a request every 5 seconds
    if (op == "get_deployments") {
        stop = setInterval('api.request("'+op+'", "deployments")', 5000);
        //setTimeout('api.request("'+op+'", "deployments")', 5000);
    }
}

// creates and sends a json message to the jsonhandler in views.py
function ImageServiceAPI() {
    this.messageFactory = new JSONMessageFactory();
    this.messageHandler = new JSONMessageHandler();

    // sends a message to the console saying that json is being sent to backend 
    this.request=function(op,opDataKey) {
        console.log("send json to backend "+op+" data structure "+opDataKey);

        // creates a JSON message using JSONMessageFactory
        jsonMessage = this.messageFactory.createRequestMessage(op,opDataKey);
        // creates and sends a request with the JSON message
        // OPSURL[op] goes through one url: '/accounts/profile/jsonhandler/'
        console.log("jsonMessage " + jsonMessage);
        this.messageHandler.request( jsonMessage , OPSURL[op] );
    };

    this.status=function() {
        console.log("status - get status from backend");
    };
}

// creates a JSON message with a JSON string of opDataKey and operation inside
function JSONMessageFactory() {
    this.createRequestMessage = function(operation,opDataKey) {
        //create json from javascript object located at opDataKey
        jsonData = JSON.stringify(DATA[opDataKey]);
        //jsonData = '[{"cirros":"alto"},{"ubuntu":"dair"}]';
        //jsonData = '{"to_deploy":[{"cirros":"alto"},{"ubuntu":"dair"}], "to_delete":[]}';
        //console.log(jsonData);
        return '{"op":"'+operation+'","deployments":'+jsonData+'}';
    };
}

// prepares the request to be sent and gets response in the callback
function JSONMessageHandler() {
    httpReq = {};

    this.request = function(jsonMessage,opurl) {
        console.log("create request to backend with json data Model at url "+jsonMessage+" "+opurl);
        // creates the Http request object
        httpUtils = new HTTPUtils();
        httpReq = httpUtils.CreateHttpObject();
        // sends the request with opurl, JSON message and callback via POST
        httpUtils.sendViaPOST(httpReq,opurl,jsonMessage,this.callback);
    };

    // creates callback to send responseText to console after final ready state
    this.callback = function() {
        if(httpReq.readyState == 4){
            var json = httpReq.responseText;
            console.log("JSON message response " + json);
            obj = JSON.parse(json);
            if (obj.errors.length != 0) {
                alert("ERROR: " + obj.errors);
            }
            response_op_handler(obj);
        }
    }

}

// POSTS the json message on httpReq
function HTTPUtils() {

    // sends a request via POST to url
    this.sendViaPOST=function(httpReq,url,jsonMsg,callback) {
        console.log("JSON message request " + jsonMsg);
        jsonMsg = encodeURIComponent(jsonMsg);
        httpReq.onreadystatechange=callback;
        httpReq.open("POST",url,true);
        httpReq.setRequestHeader("Content-type","application/x-www-form-urlencoded");
        httpReq.send("jsonMsg="+jsonMsg);
    }

    this.CreateHttpObject=function() {
        if (window.XMLHttpRequest){
            // code for IE7+, Firefox, Chrome, Opera, Safari
            return new XMLHttpRequest();
        }
        if (window.ActiveXObject){
            // code for IE6, IE5
            return new ActiveXObject("Microsoft.XMLHTTP");
        }
        return null;
    }

}

// filters response to the appropriate operation after the callback
function response_op_handler(obj) {

    if (obj.op == "get_deployments") {
        //console.log("obj.init " + obj.init);
        if (obj.init == "True") {
            console.log("first loop");
            saving = false;
            document.getElementById("spinner").innerHTML = "";
            document.getElementById("save").disabled = false;
            first_deployments = obj.deployments[0];
        }
        display_deployments();
    } else if (obj.op == "update") {
        init("get_deployments");
    }

}
