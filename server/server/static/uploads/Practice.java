import java.util.Scanner;
import java.io.IOException;

interface Base1 {
	int num1 = 10;
	void show();
}

interface Base2 {
	int num2 = 20;
	void show();
}

class Derived implements Base1, Base2 {
	int num3 = num1 + num2;
	public void show() {
		System.out.println("\nAddition of first number inherited from Base 1 (" + num1 + ") and second number inherited from Base 2 (" + num2 + ") is " + num3 + "!!!");
	}
}

public class Practice {

	public static void main(String []args) throws IOException, InterruptedException {
		Scanner sc = new Scanner(System.in);
		new ProcessBuilder("cmd","/c","cls").inheritIO().start().waitFor();
		System.out.println("\n* * * * * * * * * * * * * * *");
		System.out.println("*                           *");
		System.out.println("*    Name: Tulika Thampi    *");
		System.out.println("*                           *");
		System.out.println("*    Roll no.: T23066       *");
		System.out.println("*                           *");
		System.out.println("* * * * * * * * * * * * * * *\n");
		System.out.print("Press Enter to Continue!!! ");
		sc.nextLine();
		new ProcessBuilder("cmd","/c","cls").inheritIO().start().waitFor();

		System.out.println("Splitting A String");
		System.out.println("\n* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n");
		String choice;
		for (;;) {
			Derived obj = new Derived();
			obj.show();			
			for (;;) {
				System.out.print("\nWould you like to continue? (Yes/No) ");
				choice = sc.nextLine();
				if (choice.toUpperCase().equals("YES") || choice.toUpperCase().equals("Y")) {
					System.out.println();
					break;
				}
				else if (choice.toUpperCase().equals("NO") || choice.toUpperCase().equals("N")) {
					System.out.println("\nThank you for using this program!!!");
					System.exit(0);
				}
				else {
					System.out.println("Invalid choice!!!");
				}
			}
		}
	}
}