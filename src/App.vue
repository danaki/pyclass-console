<template>
  <v-app>
    <v-toolbar app>
      <v-toolbar-title class="headline text-uppercase">
        <span>PyClass</span>
        <span class="font-weight-light">Console</span>
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon @click="triggerTask(true)" :disabled="timers.timer.isRunning">
        <v-icon>play_arrow</v-icon>
      </v-btn>
      <v-btn icon @click="triggerTask(false)" :disabled="!timers.timer.isRunning">
        <v-icon>stop</v-icon>
      </v-btn>
    </v-toolbar>

    <v-content>
      <v-container grid-list-md text-xs-center>
        <v-layout row wrap>
          <v-flex xs6>
            <v-card>
              <v-card-title primary-title>
                <v-select
                  :items="students"
                  :item-disabled="(item) => item.online == true"
                  @change="login"
                  v-model="name"
                  item-text="name"
                  label="Your name"
                  hide-details
                ></v-select>
              </v-card-title>
              <v-card-actions>
                <v-spacer></v-spacer>

                <v-btn
                  :flat="status != 'thinking'"
                  @click="status = 'thinking'"
                  value="thinking"
                  color="info"
                  :disabled="!name"
                >Thinking...
                  <v-icon>query_builder</v-icon>
                </v-btn>
                <v-btn
                  :flat="status != 'done'"
                  @click="status = 'done'"
                  color="success"
                  :disabled="!name"
                >Done
                  <v-icon>done</v-icon>
                </v-btn>
                <v-btn
                  :flat="status != 'stuck'"
                  @click="status = 'stuck'"
                  color="warning"
                  :disabled="!name"
                >Stuck
                  <v-icon>power_off</v-icon>
                </v-btn>

                <v-spacer></v-spacer>
              </v-card-actions>
            </v-card>
          </v-flex>

          <v-flex xs6 class="timer">
            <v-card height="100%">
              <v-layout fill-height text-xs-center justify-center>
                <v-card-title primary-title>
                  <div class="v-time-picker-title">
                    <div class="v-time-picker-title__time">
                      <div class="v-picker__title__btn v-picker__title__btn--active">
                        <span v-if="timers.timer.isRunning">{{ mins }}</span>
                        <span v-else>--</span>
                      </div>
                      <span v-bind:class="{ 'white--text': runningTime % 2 }">:</span>
                      <div class="v-picker__title__btn">
                        <span v-if="timers.timer.isRunning">{{ secs }}</span>
                        <span v-else>--</span>
                      </div>
                    </div>
                  </div>
                </v-card-title>
              </v-layout>
            </v-card>
          </v-flex>
        </v-layout>

        <v-layout row wrap>
          <v-flex xs6></v-flex>
        </v-layout>
        <v-layout row wrap>
          <v-flex xs6></v-flex>
        </v-layout>

        <v-layout row wrap>
          <v-flex xs6>
            <v-data-table
              :items="students"
              item-key="name"
              hide-actions
              hide-headers
              class="elevation-1"
            >
              <template slot="items" slot-scope="props">
                <tr :active="props.item.online">
                  <td width="50%">{{ props.item.name }}</td>
                  <td width="50%">
                    <span v-if="props.item.status == 'thinking'" class="info--text">Thinking...</span>
                    <span v-if="props.item.status == 'done'" class="success--text">Done</span>
                    <span v-if="props.item.status == 'stuck'" class="warning--text">Stuck</span>
                  </td>
                </tr>
              </template>
            </v-data-table>
          </v-flex>

          <v-flex xs6>
            <v-toolbar>
              <v-text-field
                v-model="message"
                @keyup.enter.native="sendMessage"
                placeholder="Chat..."
              ></v-text-field>
            </v-toolbar>

            <v-list>
              <template v-for="message in chat">
                <v-list-tile :key="message">
                  <v-list-tile-content>
                    <v-list-tile-sub-title>
                      <span class='text--primary'>{{ message.name }}</span> &mdash; {{ message.text }}
                    </v-list-tile-sub-title>
                  </v-list-tile-content>
                </v-list-tile>
              </template>
            </v-list>
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>
  </v-app>
</template>

<script>
import io from "socket.io-client";
export default {
  data() {
    return {
      name: null,
      message: "",
      status: null,
      runningTime: 0,
      students: [],
      socket: io(process.env.VUE_APP_BACKEND_ADDRESS
        || window.location.hostname + ':' + window.location.port),
      chat: []
    };
  },
  methods: {
    sendMessage(e) {
      e.preventDefault();

      if (this.message.trim()) {
        this.socket.emit("chat_message_send", this.message);
        this.message = "";
      }
    },
    login(name) {
      this.socket.emit("login", name);
    },
    triggerTask(started) {
      this.socket.emit("trigger_task", started);
    },
    onConnect() {
      this.socket.emit("student_list_request");
      this.socket.emit("login", this.name);
    },
    onChatMessage(data) {
      this.chat = [ data, ...this.chat ];
    },
    onChatHistory(data) {
      this.chat = data
    },
    onStudentList(data) {
      this.students = data;
      data.forEach(element => {
        if (element["name"] == this.name) {
          this.status = element["status"];
        }
      });
    },
    onTaskTriggered(data) {
      if (data["started"]) {
        this.$timer.start("timer");
        this.runningTime = data["running_time"];
      } else {
        this.$timer.stop("timer");
        this.runningTime = 0;
      }
    },
    timer() {
      this.runningTime += 1;
    }
  },
  mounted() {
    this.socket.on("task_triggered", this.onTaskTriggered);
    this.socket.on("connect", this.onConnect);
    this.socket.on("chat_message_receive", this.onChatMessage);
    this.socket.on("chat_history", this.onChatHistory);
    this.socket.on("student_list", this.onStudentList);
  },
  watch: {
    status(value) {
      this.socket.emit("change_status", value);
    }
  },
  computed: {
    mins() {
      return (Array(2).join("0") + Math.floor(this.runningTime / 60)).slice(-2);
    },
    secs() {
      return (Array(2).join("0") + Math.floor(this.runningTime % 60)).slice(-2);
    }
  },
  timers: {
    timer: { repeat: true, time: 1000 }
  }
};
</script>
<style>
div.v-time-picker-title {
  color: #000;
}

div.v-time-picker-title span {
  font-size: 100px;
}

div.timer {
  margin-top: 4px;
  padding-bottom: 0px !important;
}

table.v-table tr td {
  font-size: 14px !important;
  font-weight: 800;
  text-transform: uppercase;
}
</style>
