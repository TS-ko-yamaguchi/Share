class Chat extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            logs: [],
            message: '',
            useAI: false  // 初期状態は false
        };
        this.handleChange = this.handleChange.bind(this);
        this.handleCheckboxChange = this.handleCheckboxChange.bind(this);  // 追加
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        console.log("handleChange called with value:", event.target.value);
        this.setState({message: event.target.value});
    }

    handleCheckboxChange(event) {  // 追加
        console.log("handleCheckboxChange called with checked:", event.target.checked);
        this.setState({useAI: event.target.checked});
    }

    async handleSubmit(event) {
        console.log("handleSubmit called with value:", this.state.message);
        event.preventDefault();
        const res = await axios.post('/api/chat', {message: this.state.message, useAI: this.state.useAI});  // 修正
        const logs = this.state.logs;
        logs.push({message: this.state.message, role: 'user'});
        logs.push({message: res.data.response, role: 'bot'});
        this.setState({logs: logs, message: ''});
    }

    render() {
        return (
            <div>
                <div>
                    {this.state.logs.map((log, index) => (
                        <p key={index} className={log.role}>{log.message}</p>
                    ))}
                </div>
                <form onSubmit={this.handleSubmit}>
                    <input type="text" value={this.state.message} onChange={this.handleChange} />
                    <input type="checkbox" checked={this.state.useAI} onChange={this.handleCheckboxChange} />  // 追加
                    <input type="submit" value="送信" />
                </form>
            </div>
        );
    }
}

ReactDOM.render(<Chat />, document.getElementById('chatbot'));
