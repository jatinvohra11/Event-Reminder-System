public class Event {
    private String title;
    private String description;
    private String date;
    private String time;

    public Event(String title, String description, String date, String time) {
        this.title = title;
        this.description = description;
        this.date = date;
        this.time = time;
    }

    public String getTitle() { return title; }
    public String getDate() { return date; }
    public String getTime() { return time; }

    @Override
    public String toString() {
        return title + " on " + date + " at " + time + "\n" + description;
    }
}
