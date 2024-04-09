// document.getElementById('send').addEventListener('click', function() {
//     var message = document.getElementById('message').value;
//     fetch('/api/chat', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ message: message })
//     })
//     .then(response => response.json())
//     .then(data => {
//         var chatlogs = document.getElementById('chatlogs');
//         chatlogs.innerHTML += '<p>User: ' + message + '</p>';
//         chatlogs.innerHTML += '<p>AI: ' + data.response + '</p>';
//     });
// });

// document.getElementById('message').addEventListener('keydown', function(e) {
//     if (e.ctrlKey && e.key === 'Enter') {
//         document.getElementById('send').click();
//     }
// });


import React, { useState } from 'react';

function ChatBox() {
    const [message, setMessage] = useState('');
    const [chatLogs, setChatLogs] = useState([]);

    const sendMessage = async () => {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        setChatLogs([...chatLogs, { sender: 'User', message: message }, { sender: 'AI', message: data.response }]);
        setMessage('');
    };

    return (
        <div className="chatbox">
            <div id="chatlogs">
                {chatLogs.map((chat, index) => (
                    <p key={index}>{chat.sender}: {chat.message}</p>
                ))}
            </div>
            <div className="chat-form">
                <textarea id="message" placeholder="ここにメッセージを入力してください" value={message} onChange={e => setMessage(e.target.value)}></textarea>
                <button id="send" onClick={sendMessage}>送信</button>
            </div>
        </div>
    );
}

export default ChatBox;
