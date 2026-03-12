let chat;
let msgInput;

window.onload = function () {

chat = document.getElementById("chat");
msgInput = document.getElementById("msg");

let history = JSON.parse(localStorage.getItem("chat")) || [];

/* Load old chat */
history.forEach(item => {

addMessage(item.role, item.content);

});

chat.scrollTop = chat.scrollHeight;

/* Enter key to send */
msgInput.addEventListener("keypress", function(event){
if(event.key === "Enter"){
send();
}
});

};

function scrollToBottom(){
chat.scrollTop = chat.scrollHeight;
}

function addMessage(role, content){

let className = role === "user" ? "user" : "bot";

/* Format AI text for better readability */
content = content
.replace(/\n\n/g,"<br><br>")
.replace(/\n/g,"<br>")
.replace(/- /g,"<br>• ");

chat.innerHTML += `
<div class="message ${className}">
${content}
</div>
`;

scrollToBottom();

}


/* SEND MESSAGE */

async function send(){

let msg = msgInput.value.trim();

if(msg === "") return;

addMessage("user", msg);

msgInput.value="";

chat.scrollTop = chat.scrollHeight;

/* typing indicator */

let typing = document.createElement("div");
typing.className = "message bot";
typing.id = "typing";
typing.innerText = "REBOT is typing...";
chat.appendChild(typing);

chat.scrollTop = chat.scrollHeight;

let history = JSON.parse(localStorage.getItem("chat")) || [];

try{

const response = await fetch("/chat",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
message:msg,
history:history
})
});

const data = await response.json();

document.getElementById("typing").remove();

addMessage("assistant", data.reply);

chat.scrollTop = chat.scrollHeight;

history.push({
role:"user",
content:msg
});

history.push({
role:"assistant",
content:data.reply
});

localStorage.setItem("chat", JSON.stringify(history));

}
catch(err){

document.getElementById("typing").remove();

chat.innerHTML += `<div class="message bot">Error connecting to server.</div>`;

}

}


/* CLEAR CHAT */

function clearChat(){

localStorage.removeItem("chat");

chat.innerHTML = "";

}


/* FILE UPLOAD */

async function uploadFile(){

let file = document.getElementById("fileUpload").files[0];

if(!file){
alert("Please select a file");
return;
}

let formData = new FormData();

formData.append("file",file);

addMessage("user", `Uploaded file: ${file.name}`);

chat.scrollTop = chat.scrollHeight;

try{

const res = await fetch("/upload",{
method:"POST",
body:formData
});

const data = await res.json();

addMessage("assistant", data.reply);

chat.scrollTop = chat.scrollHeight;

let history = JSON.parse(localStorage.getItem("chat")) || [];

history.push({
role:"user",
content:`Uploaded file: ${file.name}`
});

history.push({
role:"assistant",
content:data.reply
});

localStorage.setItem("chat", JSON.stringify(history));

}
catch(err){

chat.innerHTML += `<div class="message bot">Upload failed.</div>`;

}

}