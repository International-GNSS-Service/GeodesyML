package au.gov.ga.xmlschemer;

public class Violation {
    private String location;
    private String message;

    public Violation(String location, String message) {
        this.location = location;
        this.message = message;
    }

    public String getLocation() {
        return location;
    }

    public String getMessage() {
        return message;
    }

    public String toString() {
        return "location: " + getLocation() + " message: " + getMessage();
    }
}
