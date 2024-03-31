import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  providers: [DatePipe]
})
export class DashboardComponent implements OnInit {
  userName = 'Test Client';
  currentTime=  new Date();

  constructor(private datePipe: DatePipe) {}

  ngOnInit() {
    this.updateCurrentTime();
  }
  formatTime(date: Date): string {
    return this.datePipe.transform(date, 'HH:mm:ss') || '';
  }

  updateCurrentTime() {
    setInterval(() => {
      this.currentTime = new Date();
    }, 1000);
  }
}
