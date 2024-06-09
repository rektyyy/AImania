Net::Socket@ sock = null;
Net::Socket@ clientSock = null;

enum MessageType {
    SCRunStepSync = 0,
    CSetSpeed,
    CRewindToState,
    CSetInputState,
    CShutdown,
    CGiveUp,
    CExecuteCommand,
    CRequestFrame,
    SCRequestedFrameSync,
    CGetSimulationState
}

const string HOST = "127.0.0.1";
const uint16 PORT = 8002;
const uint RESPONSE_TIMEOUT = 2000;
const bool debug = true;
int next_frame_requested_W = -1;
int next_frame_requested_H = -1;
int next_frame_requested_H_low = -1;
int next_frame_requested_H_high = -1;
bool setup = true;
auto@ simManager = GetSimulationManager();

void WaitForResponse(MessageType type)
{
    auto now = Time::Now;

    while (true) {
        auto receivedType = HandleMessage();
        if (receivedType == type) {
            break;
        }

        if (receivedType == MessageType::CShutdown) {
            break;
        }

        if (receivedType == -1 && Time::Now - now > RESPONSE_TIMEOUT) {
            log("Client disconnected due to timeout (" + RESPONSE_TIMEOUT + "ms)");
            @clientSock = null;
            break;
        }
    }
}

int HandleMessage()
{
    if (clientSock.Available == 0) {
        return -1;
    }

    auto type = clientSock.ReadInt32();
    switch(type) {
        case MessageType::SCRunStepSync: {
            break;
        }

        case MessageType::CSetSpeed: {
            simManager.SetSpeed(clientSock.ReadFloat());
            break;
        }

        case MessageType::CRewindToState: {
            auto stateLength = clientSock.ReadInt32();
            auto stateData = clientSock.ReadBytes(stateLength);
            if (simManager.InRace) {
                SimulationState state(stateData);
                simManager.RewindToState(state);
            }

            break;            
        }


        case MessageType::CSetInputState: {
            int8 up   = clientSock.ReadInt8();
            int8 down = clientSock.ReadInt8();
            int steer = clientSock.ReadInt32();
            if(debug){
                log("Recieved input: UP: " + up + "DOWN: " + down + "STEER: " + steer);
            }
            if (simManager.InRace) {
                log("Set input state");
                simManager.SetInputState(InputType::Up, up);
                simManager.SetInputState(InputType::Down, down);
                if (steer != 0x7FFFFFFF) {
                    simManager.SetInputState(InputType::Steer, steer);
                }
            }

            break;
        }

        case MessageType::CShutdown: {
            log("Client disconnected");
            @clientSock = null;
            next_frame_requested_H = -1;
            break;
        }

        case MessageType::CGiveUp: {
            if(debug){
                print("Server: Give up");
            }
            if (simManager.InRace) {
                simManager.GiveUp();
            }
            break;
        }
        
        case MessageType::CExecuteCommand: {
            const int32 bytes_to_read = clientSock.ReadInt32();
            const string command = clientSock.ReadString(bytes_to_read);
            if(debug){
                print("Server: command "+command+" received");
            }
            ExecuteCommand(command);
            break;
        }

        case MessageType::CRequestFrame: {
            next_frame_requested_W = clientSock.ReadInt32();
            next_frame_requested_H = clientSock.ReadInt32();
            next_frame_requested_H_low = clientSock.ReadInt32();
            next_frame_requested_H_high = clientSock.ReadInt32();
            if(debug){
                print("Client requested next frame in size: "+next_frame_requested_W+" "+next_frame_requested_H+
                " "+next_frame_requested_H_low+ " "+next_frame_requested_H_high);
            }
            break;
        }

        case MessageType::CGetSimulationState: {
            auto@ state = simManager.SaveState();
            const auto@ data = state.ToArray();
            if(debug){
                print("Server: get_simulation_state");
            }

            clientSock.Write(int(data.Length));
            clientSock.Write(data);
            break;
        }

        case MessageType::SCRequestedFrameSync: {
            break;
        }

    }

    return type;
}

void OnRunStep(SimulationManager@ simManager)
{
    if (@clientSock is null) {
        return;
    }

    // auto@ state = simManager.SaveState();
    // auto@ data = state.ToArray();

    clientSock.Write(MessageType::SCRunStepSync);
    //clientSock.Write(data.Length);
    //clientSock.Write(data);
    WaitForResponse(MessageType::SCRunStepSync);
}

void Main()
{
    if (@sock is null) {
        @sock = Net::Socket();
        sock.Listen(HOST, PORT);
    }
}


void Render()
{   
    if (sock !is null){
        auto @newSock = sock.Accept(0);
        if (@newSock !is null) {
            @clientSock = @newSock;
            log("Client connected (IP: " + clientSock.RemoteIP + ")");
        }
        if(next_frame_requested_H >= 0){
            const auto@ frame = Graphics::CaptureScreenshot(vec2(next_frame_requested_W, next_frame_requested_H));
            array<uint8> blackWhiteFrame(next_frame_requested_W * (next_frame_requested_H_high - next_frame_requested_H_low));
            
            int counter = 0;
            for (int i = next_frame_requested_W * next_frame_requested_H_low; i < next_frame_requested_W * next_frame_requested_H_high; ++i) {
                uint8 b = frame[i * 4];
                uint8 g = frame[i * 4 + 1];
                uint8 r = frame[i * 4 + 2];
                
                // Formula for grayscale image from rgb
                uint8 gray = uint8(0.299 * r + 0.587 * g + 0.114 * b); 

                // Convert to black/white
                uint8 threshold = 85;
                if(gray < threshold) {
                    blackWhiteFrame[counter] = 255;
                }
                else {
                    blackWhiteFrame[counter] = 0;
                }
                counter++;
            }

            clientSock.Write(MessageType::SCRequestedFrameSync);
            clientSock.Write(blackWhiteFrame);
            next_frame_requested_H = -1;
            WaitForResponse(MessageType::SCRequestedFrameSync);
            if(debug){
                print("Got response from client for SCRequestedFrameSync");
            }
        }
        if(setup && clientSock !is null){
            // Change number of setup commands by hand
            for(int i = 0; i < 7; i++){
                WaitForResponse(MessageType::CExecuteCommand);
            }
            setup = false;
        }
    }
}

PluginInfo@ GetPluginInfo()
{
    PluginInfo info;
    info.Author = "rektyyy";
    info.Name = "Python <-> Trackmania";
    info.Description = "Connects game with python code";
    info.Version = "1.0.1";
    return info;
}